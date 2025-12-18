# Gradle Java setup

To keep builds portable across machines and CI, avoid hard-coding `org.gradle.java.home` in the project-level `gradle.properties`. Instead use one of these approaches:

1. **Environment-managed JDK**: Install JDK 21 and expose it via `JAVA_HOME`/`PATH`. Gradle will pick it up automatically.
2. **Gradle toolchains**: Add a toolchain block in your Gradle build to request Java 21 without requiring a specific installation path:

   ```kotlin
   java {
       toolchain {
           languageVersion.set(JavaLanguageVersion.of(21))
       }
   }
   ```

If you still need to point Gradle at a specific JDK locally, prefer a user-level `~/.gradle/gradle.properties` so the setting stays out of version control.
