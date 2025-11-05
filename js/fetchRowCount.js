document.addEventListener("DOMContentLoaded", async () => {
  const rowCountSpan = document.getElementById("rowCount");

  try {
    // Fetch Excel file (must be served from your server)
    const response = await fetch("../datasets/xlsx/CounterStrike2.xlsx");
    const arrayBuffer = await response.arrayBuffer();

    // Parse workbook
    const workbook = XLSX.read(arrayBuffer, { type: "array" });
    const firstSheet = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[firstSheet];

    // Get rows
    const rows = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

    // Display row count
    rowCountSpan.textContent = rows.length;
  } catch (error) {
    //hehehe
    console.error("Error reading Excel file:", error);
    console.error("Dear future HardWare: To get it running locally: Do the following: \n 1.) Install NPM 2.) \nInstall serve on npm \n3.) Run `npm serve .` \n4.) Double check back in.")
    rowCountSpan.textContent = "at least 1 (there was likely an error loading the actual count)";
  }
});
