plugins { id("com.android.application") }
android {
    namespace = "pro.celikom.a1exitwitness"
    compileSdk = 35
    defaultConfig {
        applicationId = "pro.celikom.a1exitwitness"
        minSdk = 28
        targetSdk = 33
        versionCode = 1
        versionName = "1.0.0-private-main-exit-only"
        // Explicit CI-only opt in; the default remains a read-only observer.
        buildConfigField("boolean", "OWN_RESOURCE_ROUTE_TRIAL",
            if (System.getenv("CELIKOM_A1_RESOURCE_NAMESPACE_TRIAL") == "1") "true" else "false")
    }
    buildFeatures { buildConfig = true }
    buildTypes { getByName("debug") { isMinifyEnabled = false } }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    packaging { resources { merges += "META-INF/xposed/*" } }
}
dependencies { compileOnly("io.github.libxposed:api:102.0.0") }
