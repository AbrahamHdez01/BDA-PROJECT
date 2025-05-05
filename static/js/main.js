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

    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - days);

    updateChartsForDateRange(startDate, endDate);

    localStorage.setItem('preferredTimeRange', timeRange);
  }

  function updateDashboardCharts(data) {
    if (data.dates && data.total_counts) {
      updateOutbreakChart(data);

      updateSeverityChart(data);

      updateRiskChart(data);
    }
  }

  function updateOutbreakChart(data) {
    const chart = getChartById('outbreakChart');
    if (chart) {
      if (data.outbreak_data && data.outbreak_data.labels && data.outbreak_data.data) {
        chart.data.labels = data.outbreak_data.labels;
        chart.data.datasets[0].data = data.outbreak_data.data;
        chart.update();
      }
    }
  }

  // Function to update the severity chart
  function updateSeverityChart(data) {
    const chart = getChartById('severityChart');
    if (chart) {
      // Update with new data if available
      if (data.severity_data && data.severity_data.labels && data.severity_data.data) {
        chart.data.labels = data.severity_data.labels;
        chart.data.datasets[0].data = data.severity_data.data;
        chart.update();
      }
    }
  }

  // Function to update the risk chart
  function updateRiskChart(data) {
    const chart = getChartById('riskChart');
    if (chart) {
      // Update with new data if available
      if (data.risk_data && data.risk_data.labels && data.risk_data.data) {
        chart.data.labels = data.risk_data.labels;
        chart.data.datasets[0].data = data.risk_data.data;
        chart.update();
      }
    }
  }

  function getChartById(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (canvas) {
      return Chart.getChart(canvas);
    }
    return null;
  }

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

  function filterChartsClientSide(startDate, endDate) {
    console.log(`Falling back to client-side filtering for date range: ${startDate.toDateString()} to ${endDate.toDateString()}`);

    const chartIds = ['severityChart', 'riskChart', 'outbreakChart'];

    chartIds.forEach(chartId => {
      const chart = getChartById(chartId);
      if (chart) {
        // For demo purposes, just update the chart title to show the date range
        if (chart.options && chart.options.plugins && chart.options.plugins.title) {
          const originalTitle = chart.options.plugins.title.text || "";
          const baseTitle = originalTitle.split(' (')[0]; // Remove any existing date range
          chart.options.plugins.title.text = `${baseTitle} (${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()})`;
          chart.update();
        }
      }
    });
  }

  const savedTimeRange = localStorage.getItem('preferredTimeRange');
  if (savedTimeRange && timeRangeDropdown) {
    timeRangeDropdown.textContent = savedTimeRange;
    setTimeout(() => loadDataForTimeRange(savedTimeRange), 500);
  }

  function resizeCharts() {
    if (window.Chart && window.Chart.instances) {
      for (let id in window.Chart.instances) {
        window.Chart.instances[id].resize();
      }
    }
  }

  window.addEventListener('resize', function () {
    resizeCharts();
  });

  const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  if (tooltips.length > 0 && typeof bootstrap !== 'undefined') {
    tooltips.forEach(tooltip => {
      new bootstrap.Tooltip(tooltip);
    });
  }

  // Helper f
  window.formatDate = function (dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, options);
  };

  window.formatNumber = function (number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  };
});

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
