async function main() {
  console.log("Hello from TypeScript + tsx + Nix!");

  // If you want to confirm ES module imports work, uncomment this:
  // const now = new Date();
  // console.log(`Current time is: ${now.toISOString()}`);
}

main().catch((err) => {
  console.error("Error in main:", err);
  process.exit(1);
});
