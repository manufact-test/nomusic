package pro.celikom.nativeprobe

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import org.json.JSONArray
import org.json.JSONObject

/** Manifest-only inventory. No credentials, metadata bundles or private service binds. */
object MediaServiceDiscovery {
    val actions = listOf("android.media.browse.MediaBrowserService", "androidx.media3.session.MediaLibraryService", "androidx.media3.session.MediaSessionService")
    data class Result(val candidates: List<ServiceInfo>, val report: JSONObject)
    fun reason(service: ServiceInfo, expectedPackage: String, effectiveEnabled: Boolean = service.enabled && service.applicationInfo?.enabled != false): String = when {
        service.packageName != expectedPackage -> "foreign_package"
        !service.exported -> "not_exported"
        !effectiveEnabled -> "disabled"
        !service.permission.isNullOrBlank() -> "permission_protected"
        else -> "eligible"
    }
    @Suppress("DEPRECATION")
    fun scan(context: Context, packageName: String = ProbeStore.YANDEX): Result {
        val pm = context.packageManager
        val report = JSONObject().put("package", packageName).put("observed_at_ms", System.currentTimeMillis())
        val flags = PackageManager.GET_SERVICES or PackageManager.MATCH_DISABLED_COMPONENTS
        val info = try { pm.getPackageInfo(packageName, flags) } catch (_: PackageManager.NameNotFoundException) {
            return Result(emptyList(),report.put("installed",false))
        }
        val actionMatches = linkedMapOf<String, MutableSet<String>>()
        val queryCounts = JSONObject()
        val enabledQueryCounts = JSONObject()
        val normallyResolvable = linkedSetOf<String>()
        val candidates = linkedMapOf<String,ServiceInfo>()
        for (action in actions) {
            val normal = pm.queryIntentServices(Intent(action).setPackage(packageName),0).mapNotNull { it.serviceInfo }.filter { it.packageName == packageName }
            enabledQueryCounts.put(action,normal.size)
            normallyResolvable.addAll(normal.map { it.name })
            val services = pm.queryIntentServices(Intent(action).setPackage(packageName), PackageManager.MATCH_DISABLED_COMPONENTS)
                .mapNotNull { it.serviceInfo }.filter { it.packageName == packageName }
            queryCounts.put(action, services.size)
            for (service in services) {
                actionMatches.getOrPut(service.name) { linkedSetOf() }.add(action)
                if (service.name in normallyResolvable && reason(service,packageName,true)=="eligible") candidates[service.name] = service
            }
        }
        val declared = info.services?.toList() ?: emptyList()
        val rows = JSONArray()
        for (service in declared.sortedBy { it.name }.take(60)) {
            val setting = try { pm.getComponentEnabledSetting(ComponentName(packageName,service.name)) } catch (_: RuntimeException) { null }
            val mediaAction = actionMatches[service.name]?.isNotEmpty() == true
            val effective = if (mediaAction) service.name in normallyResolvable else when (setting) {
                PackageManager.COMPONENT_ENABLED_STATE_ENABLED -> true
                PackageManager.COMPONENT_ENABLED_STATE_DISABLED,PackageManager.COMPONENT_ENABLED_STATE_DISABLED_USER,PackageManager.COMPONENT_ENABLED_STATE_DISABLED_UNTIL_USED -> false
                else -> service.enabled && service.applicationInfo?.enabled != false
            }
            rows.put(JSONObject().put("name",ProbeStore.clean(service.name)).put("exported",service.exported)
                .put("enabled",effective).put("manifest_enabled",service.enabled)
                .put("component_enabled_setting",setting ?: JSONObject.NULL).put("normal_media_query_match",service.name in normallyResolvable)
                .put("permission",ProbeStore.clean(service.permission) ?: JSONObject.NULL)
                .put("eligibility",reason(service,packageName,effective))
                .put("media_actions",JSONArray(actionMatches[service.name]?.toList() ?: emptyList<String>())))
        }
        report.put("installed",true).put("query_counts",queryCounts).put("enabled_query_counts",enabledQueryCounts).put("declared_service_count",declared.size)
            .put("declared_services",rows).put("truncated",declared.size>60)
            .put("eligible_media_service_count",candidates.size).put("connection_attempt_limit",3)
        return Result(candidates.values.take(3),report)
    }
}
