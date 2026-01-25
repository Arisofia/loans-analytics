// Removed 'async' to match expected synchronous behavior
export function createFigmaKPIDashboard(data: any) {
  console.log('Mocking Figma KPI Dashboard creation with data:', data);

  return {
    success: true,
    fileKey: 'mock-figma-file-key',
    url: 'https://www.figma.com/file/mock-figma-file-key',
    total_metrics: 12, // Added to satisfy usage in route.ts
    metadata: {} as any // Added to allow metadata assignment
  };
}
