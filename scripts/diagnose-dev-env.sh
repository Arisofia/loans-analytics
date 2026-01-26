#!/bin/zsh
# Automated diagnostics for Zencoder, Java, Gradle, Minikube, and Kubectl

echo "\n=== Zencoder Extension Binary Check ==="
EXT_DIR=~/.vscode/extensions
BIN_NAME=zencoder-cli
EXT_PATTERN="zencoderai.zencoder-*"
BIN_PATH=$(find $EXT_DIR/$EXT_PATTERN/out/ -name $BIN_NAME 2>/dev/null | head -n 1)
if [[ -z "$BIN_PATH" ]]; then
  echo "Zencoder CLI binary NOT FOUND."
else
  echo "Zencoder CLI binary found: $BIN_PATH"
  ls -l "$BIN_PATH"
  if [[ -x "$BIN_PATH" ]]; then
    echo "Binary is executable."
  else
    echo "Binary is NOT executable."
  fi
fi

echo "\n=== Java Diagnostics ==="
echo "JAVA_HOME: $JAVA_HOME"
java -version 2>&1 || echo "Java not found in PATH."

echo "\n=== Gradle Diagnostics ==="
gradle --version 2>&1 || echo "Gradle not found in PATH."

if [[ -f ./gradlew ]]; then
  echo "\nFound ./gradlew. Running ./gradlew --version:"
  ./gradlew --version 2>&1
fi

echo "\n=== Minikube Diagnostics ==="
which minikube || echo "minikube not found in PATH."
minikube version 2>&1 || echo "minikube not installed or not working."

echo "\n=== Kubectl Diagnostics ==="
which kubectl || echo "kubectl not found in PATH."
kubectl version --client 2>&1 || echo "kubectl not installed or not working."

echo "\n=== PATH Environment Variable ==="
echo $PATH

echo "\nDiagnostics complete. Review the output above for any errors or missing tools."
