function shouldShowPieChart(query: string) {
    // The regex checks (case-insensitive) that "show" and "pie chart" (or "piechart") appear in the query.
    const regex = /(?=.*\bshow\b)(?=.*\bpie[\s-]?chart\b)/i;
    return regex.test(query);
  }

function shouldShowBarChart(query: string): boolean {
    // The regex checks (case-insensitive) that "show" appears,
    // and that "bar" is followed by zero or more non-word characters,
    // then either "chart" or "graph". This covers "bar chart", "bar-chart", "bar graph", "bar-graph", and "bargraph".
    const regex = /(?=.*\bshow\b)(?=.*\bbar\W*(?:chart|graph)\b)/i;
    return regex.test(query);
  }
  

  export { shouldShowPieChart, shouldShowBarChart }