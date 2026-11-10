plugins { id("com.android.application") }
android {
    namespace = "pro.celikom.nativegate"
    compileSdk = 35
    defaultConfig {
        applicationId = "pro.celikom.nativegate"
        minSdk = 30
        targetSdk = 33
        versionCode = 1
        versionName = "0.1-public-session-gate"
    }
    buildTypes {
        getByName("release") { isMinifyEnabled = false }
        getByName("debug") { isMinifyEnabled = false }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
dependencies {
    implementation("androidx.media3:media3-session:1.6.1")
}
