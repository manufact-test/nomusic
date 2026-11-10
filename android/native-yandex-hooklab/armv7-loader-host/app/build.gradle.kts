plugins { id("com.android.application") }
android {
    namespace = "pro.celikom.armv7loaderhost"
    compileSdk = 35
    defaultConfig {
        // Only the explicitly approved isolated witness ID can override the base lab app.
        val witnessId = providers.gradleProperty("celikomWitnessAppId").orNull
        require(witnessId == null || witnessId == "pro.celikom.armv7loaderhost.witness")
        val audioId = providers.gradleProperty("celikomAudioAppId").orNull
        require(audioId == null || audioId == "pro.celikom.armv7loaderhost.audio")
        require(witnessId == null || audioId == null)
        // Separate, unprivileged OWN-only x86_64 emulator CI build.
        // Never replaces the normal ARMv7 artifact, does not touch Yandex.
        val ownEmulator = providers.gradleProperty("celikomOwnEmulator").orNull
        require(ownEmulator == null || ownEmulator == "true")
        require(ownEmulator == null || (witnessId == null && audioId == null))
        applicationId = if (ownEmulator != null) "pro.celikom.armv7loaderhost.audio"
            else audioId ?: witnessId ?: "pro.celikom.armv7loaderhost"
        manifestPlaceholders["celikomLabLabel"] = if (audioId != null || ownEmulator != null) "CELIKOM Audio Smoke Test" else if (witnessId == null) "CELIKOM ARM Loader Lab" else "CELIKOM ARM Hook Witness"
        minSdk = 28
        targetSdk = 33
        versionCode = 1
        versionName = "0.1.0-arm-loader-only"
        ndk { abiFilters += if (ownEmulator != null) listOf("x86_64") else listOf("armeabi-v7a") }
    }
    externalNativeBuild { cmake { path = file("src/main/cpp/CMakeLists.txt") } }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
