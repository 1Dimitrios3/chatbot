function shouldShowPieChart(query: string) {
    // The regex checks (case-insensitive) that "show" and "pie chart" (or "piechart") appear in the query.
    const regex = /(?=.*\bshow\b)(?=.*\bpie[\s-]?chart\b)/i;
    return regex.test(query);
  }

  export { shouldShowPieChart }