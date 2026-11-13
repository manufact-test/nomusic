package pro.celikom.nativeprobe

import android.content.ComponentName
import android.content.Intent
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.zip.ZipEntry
import java.util.zip.ZipFile
import java.util.zip.ZipOutputStream

@RunWith(AndroidJUnit4::class)
class IdentitySourceTest {
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val context = instrumentation.targetContext

    @Test fun legacyTransportReadsSourceIdWithoutCommandsAndExpiresPreviousProcess() {
        ProbeStore.clear(context); ProbeStore.setEnabled(context, true)
        lateinit var probe: LegacyIdentityProbe
        instrumentation.runOnMainSync {
            probe = LegacyIdentityProbe(context, context.packageName)
            probe.connect(ComponentName(context, LegacyLibraryFixture::class.java))
        }
        try {
            val deadline = android.os.SystemClock.elapsedRealtime() + 7000
            var evidence = ProbeStore.report(context).getJSONObject("legacy_identity")
            while (evidence.optString("status") != "connected" && android.os.SystemClock.elapsedRealtime() < deadline) {
                android.os.SystemClock.sleep(100)
                evidence = ProbeStore.report(context).getJSONObject("legacy_identity")
            }
            assertEquals("connected", evidence.optString("status")); assertTrue(evidence.getBoolean("fresh"))
            assertEquals("141103805", evidence.getJSONObject("metadata").getString(android.media.MediaMetadata.METADATA_KEY_MEDIA_ID))
            assertEquals("141103805", evidence.getJSONObject("current_queue_item").getJSONObject("media_uri").getString("track_id_candidate"))
            assertEquals(0, evidence.getInt("commands_sent")); assertFalse(evidence.getBoolean("exact_track_id_verified"))
            assertFalse(evidence.toString().contains("private-fixture"))
            evidence.put("process_instance", "old-process")
            ProbeStore.put(context, "legacy_identity", evidence)
            val expired = ProbeStore.report(context).getJSONObject("legacy_identity")
            assertFalse(expired.getBoolean("fresh")); assertEquals("data_stale", expired.getString("status"))
            instrumentation.runOnMainSync { probe.stop() }
            assertEquals("stopped", ProbeStore.report(context).getJSONObject("legacy_identity").getString("status"))
        } finally {
            instrumentation.runOnMainSync { probe.stop(); context.stopService(Intent(context, LegacyLibraryFixture::class.java)) }
            ProbeStore.clear(context)
        }
    }

    @Test fun packageArchiveIncludesOnlyStaticCodeAndResourcesAcrossSplits() {
        val directory = File(context.cacheDir, "export-test").apply { mkdirs() }
        fun source(name: String, entries: Map<String, String>): File = File(directory, name).also { file ->
            ZipOutputStream(file.outputStream()).use { zip ->
                entries.forEach { (key, value) -> zip.putNextEntry(ZipEntry(key)); zip.write(value.toByteArray()); zip.closeEntry() }
            }
        }
        val base = source("base.apk", mapOf("classes.dex" to "code", "AndroidManifest.xml" to "manifest", "resources.arsc" to "resources",
            "assets/token.txt" to "private-account", "shared_prefs/auth.xml" to "private-account", "nested/classes2.dex" to "private-account"))
        val split = source("feature.apk", mapOf("classes2.dex" to "split code", "res/raw/music.mp3" to "private-account"))
        val output = File(directory, "program.zip")
        try {
            YandexPackageExport.writeArchive(listOf(base, split), output, JSONObject().put("account_data_included", false))
            ZipFile(output).use { zip ->
                val names = zip.entries().asSequence().map { it.name }.toSet()
                assertEquals(setOf("base/classes.dex", "base/AndroidManifest.xml", "base/resources.arsc", "split-1/classes2.dex", "export-info.json"), names)
                assertEquals("code", zip.getInputStream(zip.getEntry("base/classes.dex")).bufferedReader().readText())
                val info = JSONObject(zip.getInputStream(zip.getEntry("export-info.json")).bufferedReader().readText())
                assertFalse(info.getBoolean("account_data_included")); assertEquals(4, info.getJSONArray("entries").length())
                assertFalse(info.toString().contains("private-account"))
            }
            assertFalse(YandexPackageExport.allowed("lib/arm64-v8a/classes.dex"))
            assertFalse(YandexPackageExport.allowed("../classes2.dex"))
            assertFalse(YandexPackageExport.allowed("classes1.dex")); assertTrue(YandexPackageExport.allowed("classes10.dex"))
        } finally { directory.deleteRecursively() }
    }

    @Test fun packageArchiveRejectsMissingCodeAndRemovesPartialOutput() {
        val directory = File(context.cacheDir, "export-reject-test").apply { mkdirs() }
        val source = File(directory, "empty.apk")
        val output = File(directory, "partial.zip")
        try {
            ZipOutputStream(source.outputStream()).use { zip -> zip.putNextEntry(ZipEntry("AndroidManifest.xml")); zip.write(byteArrayOf(1)); zip.closeEntry() }
            try { YandexPackageExport.writeArchive(listOf(source), output, JSONObject()); fail("Missing DEX must reject") }
            catch (_: java.io.IOException) { }
            assertFalse(output.exists())
        } finally { directory.deleteRecursively() }
    }
}
