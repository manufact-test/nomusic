plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
val releaseKey = System.getenv("CELIKOM_ANDROID_KEYSTORE")
android {
    namespace = "pro.celikom.nativeprobe"
    compileSdk = 36
    defaultConfig {
        applicationId = "pro.celikom.nativeprobe"; minSdk = 28; targetSdk = 36
        versionCode = 3; versionName = "0.3.2-probe"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    signingConfigs {
        create("distribution") {
            if (!releaseKey.isNullOrBlank()) {
                storeFile = file(releaseKey)
                storePassword = System.getenv("CELIKOM_ANDROID_STORE_PASSWORD")
                keyAlias = System.getenv("CELIKOM_ANDROID_KEY_ALIAS")
                keyPassword = System.getenv("CELIKOM_ANDROID_KEY_PASSWORD")
            }
        }
    }
    buildTypes { getByName("release") { signingConfig = signingConfigs.getByName("distribution") } }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    implementation("androidx.core:core:1.13.1")
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    androidTestImplementation("androidx.test:runner:1.7.0")
}

// Never silently deliver a release signed by another ephemeral debug key.
gradle.taskGraph.whenReady {
    if (allTasks.any { it.name == "validateSigningRelease" }) {
        check(!releaseKey.isNullOrBlank() && listOf("CELIKOM_ANDROID_STORE_PASSWORD", "CELIKOM_ANDROID_KEY_ALIAS", "CELIKOM_ANDROID_KEY_PASSWORD").all { !System.getenv(it).isNullOrBlank() }) {
            "Distribution requires the owner's persistent signing key in private build secrets"
        }
    }
}
