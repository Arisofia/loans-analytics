plugins {
    id("java")
    application
    id("org.springframework.boot") version "3.2.3"
    id("io.spring.dependency-management") version "1.1.4"
}

group = "com.abaco"
version = "0.0.1-SNAPSHOT"

repositories {
    mavenCentral()
}

// Enforce a compatible Java version for this project to ensure reproducible builds.
// This directly fixes the "Unsupported class file major version" error.
java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(17))
    }
}

application {
    mainClass.set("com.abaco.Main")
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web:3.2.3")
    implementation("org.springframework.boot:spring-boot-starter-oauth2-client:3.2.3")
    testImplementation("org.springframework.boot:spring-boot-starter-test:3.2.3")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher:1.10.2")
}
