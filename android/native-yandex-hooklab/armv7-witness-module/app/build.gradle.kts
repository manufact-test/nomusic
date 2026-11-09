plugins { id("com.android.application") }
android {
    namespace = "pro.celikom.armv7witnessmodule"
    compileSdk = 35
    defaultConfig {
        applicationId = "pro.celikom.armv7witnessmodule"
        minSdk = 28
        targetSdk = 33
        versionCode = 1
        versionName = "0.0.1-own-arm-hook-witness"
    }
    buildTypes {
        getByName("debug") { isMinifyEnabled = false }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    packaging { resources { merges += "META-INF/xposed/*" } }
}
dependencies { compileOnly("io.github.libxposed:api:102.0.0") }
