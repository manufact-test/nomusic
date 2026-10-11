plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "pro.celikom.researchcontroller"
    compileSdk = 36
    defaultConfig {
        applicationId = "pro.celikom.researchcontroller"; minSdk = 28; targetSdk = 36
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    androidTestImplementation("androidx.test:runner:1.7.0")
}
