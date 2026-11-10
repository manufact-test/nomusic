plugins { id("com.android.application") }
android {
    namespace = "pro.celikom.ownedplayer"
    compileSdk = 35
    defaultConfig {
        applicationId = "pro.celikom.ownedplayer"
        minSdk = 30
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0-dev"
    }
    buildTypes {
        getByName("release") { isMinifyEnabled = false }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
dependencies {
    implementation("androidx.media3:media3-exoplayer:1.6.1")
    implementation("androidx.media3:media3-session:1.6.1")
    implementation("androidx.media3:media3-datasource:1.6.1")
}
