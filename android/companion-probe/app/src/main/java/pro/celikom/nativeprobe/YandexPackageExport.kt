package pro.celikom.nativeprobe

import android.content.Context
import android.content.pm.PackageManager
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.util.zip.ZipEntry
import java.util.zip.ZipFile
import java.util.zip.ZipOutputStream

/** Static installed program files only. Never opens dataDir, preferences, cache or account storage. */
object YandexPackageExport {
    private const val MAX_RAW_BYTES = 200L * 1024 * 1024
    private const val MAX_ENTRIES = 128
    internal fun allowed(name: String): Boolean = name == "AndroidManifest.xml" || name == "resources.arsc" ||
        Regex("classes(?:[2-9]|[1-9][0-9]+)?\\.dex").matches(name)

    @Synchronized fun create(context: Context): File {
        @Suppress("DEPRECATION")
        val info = context.packageManager.getPackageInfo(ProbeStore.YANDEX, 0)
        val app = info.applicationInfo ?: throw IOException("package_unavailable")
        val sources = (listOf(app.sourceDir) + (app.splitSourceDirs?.toList() ?: emptyList())).distinct()
        check(sources.size <= 64)
        val directory = File(context.cacheDir, "package-export").apply { mkdirs() }
        // Limit previous static exports without touching any other cache directory.
        directory.listFiles()?.filter { it.isFile && it.name.startsWith("yandex-code-") && it.extension == "zip" }
            ?.filter { System.currentTimeMillis() - it.lastModified() > 24L * 60 * 60 * 1000 }
            ?.forEach { it.delete() }
        val output = File(directory, "yandex-code-${android.os.SystemClock.elapsedRealtime()}.zip")
        val result = writeArchive(sources.map { File(it) }, output, JSONObject()
            .put("schema", 1).put("package", ProbeStore.YANDEX).put("version", info.versionName)
            .put("version_code", info.longVersionCode).put("generated_at_ms", System.currentTimeMillis())
            .put("content", "installed_program_only").put("account_data_included", false))
        ProbeStore.put(context, "package_export", JSONObject().put("status", "ready")
            .put("bytes", result.length()).put("account_data_included", false))
        return result
    }

    internal fun writeArchive(sources: List<File>, output: File, metadata: JSONObject): File {
        var total = 0L
        var count = 0
        var dexCount = 0
        val entries = JSONArray()
        try {
            ZipOutputStream(output.outputStream().buffered()).use { result ->
                result.setLevel(1)
                sources.forEachIndexed { index, source ->
                    ZipFile(source).use { apk ->
                        val iterator = apk.entries()
                        val seen = mutableSetOf<String>()
                        while (iterator.hasMoreElements()) {
                            val entry = iterator.nextElement()
                            if (entry.isDirectory || !allowed(entry.name)) continue
                            if (!seen.add(entry.name)) throw IOException("duplicate_program_entry")
                            if (++count > MAX_ENTRIES || entry.size > MAX_RAW_BYTES) throw IOException("program_limit")
                            val name = "${if (index == 0) "base" else "split-$index"}/${entry.name}"
                            result.putNextEntry(ZipEntry(name))
                            var written = 0L
                            apk.getInputStream(entry).use { input ->
                                val buffer = ByteArray(65536)
                                while (true) {
                                    val size = input.read(buffer)
                                    if (size < 0) break
                                    total += size; written += size
                                    if (total > MAX_RAW_BYTES) throw IOException("program_limit")
                                    result.write(buffer, 0, size)
                                }
                            }
                            result.closeEntry()
                            if (entry.name.endsWith(".dex")) dexCount++
                            entries.put(JSONObject().put("name", name).put("bytes", written))
                        }
                    }
                }
                if (dexCount == 0) throw IOException("no_program_code")
                metadata.put("entries", entries).put("raw_bytes", total)
                result.putNextEntry(ZipEntry("export-info.json"))
                result.write(metadata.toString(2).toByteArray(Charsets.UTF_8))
                result.closeEntry()
            }
            return output
        } catch (error: Exception) {
            output.delete()
            throw error
        }
    }
}
