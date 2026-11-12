plugins { id("com.android.application") }
android {
    namespace = "pro.celikom.a1clonecontrol"
    compileSdk = 35
    defaultConfig {
        applicationId = "pro.celikom.a1clonecontrol"
        minSdk = 28
        targetSdk = 33
        versionCode = 1
        versionName = "1.0.0-ephemeral-empty-module"
    }
    buildTypes { getByName("debug") { isMinifyEnabled = false } }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    packaging { resources { merges += "META-INF/xposed/*" } }
}
dependencies { compileOnly("io.github.libxposed:api:102.0.0") }
