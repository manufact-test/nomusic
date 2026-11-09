plugins { id("com.android.application") }
android {
    namespace = "pro.celikom.armv7loaderhost"
    compileSdk = 35
    defaultConfig {
        applicationId = "pro.celikom.armv7loaderhost"
        minSdk = 28
        targetSdk = 33
        versionCode = 1
        versionName = "0.1.0-arm-loader-only"
        ndk { abiFilters += listOf("armeabi-v7a") }
    }
    externalNativeBuild { cmake { path = file("src/main/cpp/CMakeLists.txt") } }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
