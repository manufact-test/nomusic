plugins { id("com.android.application") }
android {
    namespace = "pro.celikom.nativepublicsession"
    compileSdk = 35
    defaultConfig {
        applicationId = "pro.celikom.nativepublicsession"
        minSdk = 30
        targetSdk = 33
        versionCode = 1
        versionName = "readonly-session-probe"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
dependencies {
    implementation("androidx.media3:media3-session:1.6.1")
}
