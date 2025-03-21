// Main JavaScript for MediDash

document.addEventListener('DOMContentLoaded', function () {
  // Toggle sidebar
  const sidebarToggle = document.getElementById('sidebarCollapse');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function () {
      document.getElementById('sidebar').classList.toggle('active');
    });
  }

  // Time range dropdown functionality
  const timeRangeDropdown = document.getElementById('timeRangeDropdown');
  if (timeRangeDropdown) {
    const timeRangeItems = document.querySelectorAll('.dropdown-menu .dropdown-item');
    timeRangeItems.forEach(item => {
      item.addEventListener('click', function (e) {
        e.preventDefault();
        const selectedRange = this.textContent;
        timeRangeDropdown.textContent = selectedRange;
        loadDataForTimeRange(selectedRange);
      });
    });
  }

  // Function to load data based on selected time range
  function loadDataForTimeRange(timeRange) {
    console.log(`Loading data for time range: ${timeRange}`);

    // Parse the selected time range
    let days = 30; // Default to 30 days
    if (timeRange.includes('7')) {
      days = 7;
    } else if (timeRange.includes('30')) {
      days = 30;
    } else if (timeRange.includes('90')) {
      days = 90;
    } else if (timeRange.includes('All')) {
      days = 365; // Use a large number for "All Time"
    }

    // Get today's date
    const endDate = new Date();
    // Calculate start date based on selected time range
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - days);

    // Filter datasets for each chart based on the date range
    updateChartsForDateRange(startDate, endDate);

    // Save the user's preference
    localStorage.setItem('preferredTimeRange', timeRange);
  }

  // Function to update charts with new data from API
  function updateDashboardCharts(data) {
    // Update each chart with its corresponding data
    if (data.dates && data.total_counts) {
      updateTimeSeriesChart(data.dates, data.total_counts, data.severity_data);
    }
  }

  // Function to update the time series chart with new data
  function updateTimeSeriesChart(dates, counts, severityData) {
    const timeSeriesChart = getChartById('timeSeriesChart');
    if (timeSeriesChart) {
      timeSeriesChart.data.labels = dates;
      timeSeriesChart.data.datasets[0].data = counts;

      // If we have severity breakdown, update those datasets too
      if (severityData) {
        const severities = Object.keys(severityData);
        for (let i = 0; i < severities.length; i++) {
          if (timeSeriesChart.data.datasets[i + 1]) {
            timeSeriesChart.data.datasets[i + 1].data = severityData[severities[i]];
          }
        }
      }

      timeSeriesChart.update();
    }
  }

  // Helper function to get Chart.js instance by canvas ID
  function getChartById(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (canvas) {
      const chartId = Object.keys(Chart.instances).find(
        id => Chart.instances[id].canvas.id === canvasId
      );
      return chartId ? Chart.instances[chartId] : null;
    }
    return null;
  }

  // Apply the filtering to all charts on the page
  function updateChartsForDateRange(startDate, endDate) {
    // Request updated data from the server
    fetch(`/dashboard/api/disease-trends/?start=${startDate.toISOString()}&end=${endDate.toISOString()}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch updated data');
        }
        return response.json();
      })
      .then(data => {
        // Update all charts with new data
        updateDashboardCharts(data);
      })
      .catch(error => {
        console.error('Error updating charts:', error);

        // Fallback to filtering client-side for demo purposes
        filterChartsClientSide(startDate, endDate);
      });
  }

  // Client-side filtering as fallback (or for demo without backend)
  function filterChartsClientSide(startDate, endDate) {
    if (window.Chart && window.Chart.instances) {
      for (let id in window.Chart.instances) {
        const chart = window.Chart.instances[id];

        // Skip charts that don't have time-based data
        if (chart.config.type === 'pie' || chart.config.type === 'doughnut' || chart.config.type === 'radar') {
          continue;
        }

        // For demo, we'll just update the visible range for line/bar charts
        if (chart.config.type === 'line' || chart.config.type === 'bar') {
          // Generate new sample data
          const labels = [];
          const data = [];

          for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
            labels.push(d.toLocaleDateString());
            data.push(Math.floor(Math.random() * 100) + 20);
          }

          // Update chart data
          chart.data.labels = labels;
          if (chart.data.datasets.length > 0) {
            chart.data.datasets[0].data = data;

            // If there's a second dataset (prediction data), generate that too
            if (chart.data.datasets.length > 1) {
              const predictionData = data.map(val => Math.floor(val * (1 + Math.random() * 0.4 - 0.1)));
              chart.data.datasets[1].data = predictionData;
            }
          }

          chart.update();
        }
      }
    }
  }

  // Check for saved preference on page load
  const savedTimeRange = localStorage.getItem('preferredTimeRange');
  if (savedTimeRange && timeRangeDropdown) {
    timeRangeDropdown.textContent = savedTimeRange;
    setTimeout(() => loadDataForTimeRange(savedTimeRange), 500);
  }

  // Set up responsive behavior for charts
  function resizeCharts() {
    if (window.Chart && window.Chart.instances) {
      for (let id in window.Chart.instances) {
        window.Chart.instances[id].resize();
      }
    }
  }

  // Call resize on window resize
  window.addEventListener('resize', function () {
    resizeCharts();
  });

  // Initialize tooltips
  const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  if (tooltips.length > 0 && typeof bootstrap !== 'undefined') {
    tooltips.forEach(tooltip => {
      new bootstrap.Tooltip(tooltip);
    });
  }

  // Helper function to format dates for display
  window.formatDate = function (dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, options);
  };

  // Helper function to format numbers with commas
  window.formatNumber = function (number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  };
});

// Function to load data via AJAX (for future use)
function loadDashboardData(endpoint, callback) {
  fetch(endpoint)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      if (callback && typeof callback === 'function') {
        callback(data);
      }
    })
    .catch(error => {
      console.error('Error fetching dashboard data:', error);
    });
}

// Default chart colors
const chartColors = {
  primary: 'rgba(78, 115, 223, 0.8)',
  success: 'rgba(40, 167, 69, 0.8)',
  warning: 'rgba(255, 193, 7, 0.8)',
  danger: 'rgba(220, 53, 69, 0.8)',
  info: 'rgba(23, 162, 184, 0.8)',
  secondary: 'rgba(108, 117, 125, 0.8)',
  light: 'rgba(248, 249, 250, 0.8)',
  dark: 'rgba(52, 58, 64, 0.8)'
};

// Default chart options for consistency
const defaultChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        padding: 20,
        boxWidth: 12
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      padding: 10,
      cornerRadius: 4,
      titleFont: {
        size: 14
      },
      bodyFont: {
        size: 12
      }
    }
  }
};
