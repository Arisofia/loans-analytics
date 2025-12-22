const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

async function downloadCascadePlanB() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const cookieName = process.env.CASCADE_COOKIE_NAME || "session";
  await context.addCookies([
    {
      name: cookieName,
      value: process.env.CASCADE_SESSION_COOKIE,
      domain: ".cascadedebt.com",
      path: "/",
      httpOnly: true,
      secure: true,
      sameSite: "Lax",
    },
  ]);

  const downloadsDir = path.resolve("downloads");
  fs.mkdirSync(downloadsDir, { recursive: true });

  const page = await context.newPage();
  page.setDefaultTimeout(120000);
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.goto(process.env.CASCADE_EXPORT_URL),
  ]);

  const targetPath = path.join(downloadsDir, download.suggestedFilename());
  await download.saveAs(targetPath);
  console.log(`Cascade download saved to ${targetPath}`);

  await browser.close();
}

if (!process.env.CASCADE_SESSION_COOKIE || !process.env.CASCADE_EXPORT_URL) {
  console.error("Missing CASCADE_SESSION_COOKIE or CASCADE_EXPORT_URL");
  process.exit(1);
}

downloadCascadePlanB().catch((error) => {
  console.error("Cascade Plan B failure", error);
  process.exit(1);
});
