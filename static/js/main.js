// Main JavaScript for MediDash - Optimized for performance

// Use a self-executing function to avoid polluting the global namespace
(function() {
  // Store DOM references to avoid repeated lookups
  let sidebarToggle, timeRangeDropdown, timeRangeItems;
  let chartCache = {};

  // Debounce function to limit the rate at which a function can fire
  function debounce(func, wait) {
    let timeout;
    return function() {
      const context = this, args = arguments;
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(context, args), wait);
    };
  }

  // Initialize the application when DOM is ready
  document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements
    sidebarToggle = document.getElementById('sidebarCollapse');
    timeRangeDropdown = document.getElementById('timeRangeDropdown');

    // Initialize sidebar toggle
    if (sidebarToggle) {
      sidebarToggle.addEventListener('click', function() {
        document.getElementById('sidebar').classList.toggle('active');
      });
    }

    // Initialize time range dropdown
    if (timeRangeDropdown) {
      timeRangeItems = document.querySelectorAll('.dropdown-menu .dropdown-item');
      timeRangeItems.forEach(item => {
        item.addEventListener('click', function(e) {
          e.preventDefault();
          const selectedRange = this.textContent;
          timeRangeDropdown.textContent = selectedRange;
          loadDataForTimeRange(selectedRange);
        });
      });

      // Load saved time range preference
      const savedTimeRange = localStorage.getItem('preferredTimeRange');
      if (savedTimeRange && timeRangeDropdown) {
        timeRangeDropdown.textContent = savedTimeRange;
        // Use requestAnimationFrame to defer non-critical operations
        requestAnimationFrame(() => {
          loadDataForTimeRange(savedTimeRange);
        });
      }
    }

    // Initialize resize handler with debounce
    window.addEventListener('resize', debounce(resizeCharts, 250));

    // Initialize tooltips
    initTooltips();
  });

  // Function to load data based on selected time range
  function loadDataForTimeRange(timeRange) {
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

  // Function to update all dashboard charts with new data
  function updateDashboardCharts(data) {
    if (!data.dates || !data.total_counts) return;

    // Use requestAnimationFrame to optimize visual updates
    requestAnimationFrame(() => {
      // Batch chart updates to reduce layout thrashing
      const chartsToUpdate = ['outbreakChart', 'severityChart', 'riskChart'];

      chartsToUpdate.forEach(chartId => {
        const chart = getChartById(chartId);
        if (!chart) return;

        // Update chart data based on chart type
        if (chartId === 'outbreakChart' && data.outbreak_data) {
          updateChartData(chart, data.outbreak_data.labels, data.outbreak_data.data);
        } else if (chartId === 'severityChart' && data.severity_data) {
          updateChartData(chart, data.severity_data.labels, data.severity_data.data);
        } else if (chartId === 'riskChart' && data.risk_data) {
          updateChartData(chart, data.risk_data.labels, data.risk_data.data);
        }
      });
    });
  }

  // Helper function to update chart data
  function updateChartData(chart, labels, data) {
    if (!labels || !data) return;

    chart.data.labels = labels;
    chart.data.datasets[0].data = data;
    chart.update();
  }

  // Get chart by ID with caching for performance
  function getChartById(canvasId) {
    // Check cache first
    if (chartCache[canvasId]) {
      return chartCache[canvasId];
    }

    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    const chart = Chart.getChart(canvas);
    if (chart) {
      // Cache the chart reference
      chartCache[canvasId] = chart;
    }
    return chart;
  }

  // Function to update charts for a date range
  function updateChartsForDateRange(startDate, endDate) {
    // Show loading indicator
    showLoading(true);

    // Use a cached version if available
    const cacheKey = `chart_data_${startDate.toISOString()}_${endDate.toISOString()}`;
    const cachedData = sessionStorage.getItem(cacheKey);

    if (cachedData) {
      try {
        const data = JSON.parse(cachedData);
        updateDashboardCharts(data);
        showLoading(false);
        return;
      } catch (e) {
        console.error('Error parsing cached data:', e);
        // Continue with fetch if cache parsing fails
      }
    }

    // Request updated data from the server
    fetch(`/dashboard/api/disease-trends/?start=${startDate.toISOString()}&end=${endDate.toISOString()}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch updated data');
        }
        return response.json();
      })
      .then(data => {
        // Cache the response
        try {
          sessionStorage.setItem(cacheKey, JSON.stringify(data));
        } catch (e) {
          console.warn('Failed to cache chart data:', e);
        }

        // Update all charts with new data
        updateDashboardCharts(data);
        showLoading(false);
      })
      .catch(error => {
        console.error('Error updating charts:', error);
        showLoading(false);

        // Fallback to filtering client-side for demo purposes
        filterChartsClientSide(startDate, endDate);
      });
  }

  // Function to handle client-side filtering as a fallback
  function filterChartsClientSide(startDate, endDate) {
    console.log(`Falling back to client-side filtering for date range: ${startDate.toDateString()} to ${endDate.toDateString()}`);

    // Use the cached chart references for better performance
    const chartIds = ['severityChart', 'riskChart', 'outbreakChart'];

    // Batch DOM operations to reduce layout thrashing
    requestAnimationFrame(() => {
      chartIds.forEach(chartId => {
        const chart = getChartById(chartId);
        if (!chart) return;

        // For demo purposes, just update the chart title to show the date range
        if (chart.options?.plugins?.title) {
          const originalTitle = chart.options.plugins.title.text || "";
          const baseTitle = originalTitle.split(' (')[0]; // Remove any existing date range
          chart.options.plugins.title.text = `${baseTitle} (${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()})`;
          chart.update('none'); // Use 'none' animation for better performance
        }
      });
    });
  }

  // Function to resize all charts efficiently
  function resizeCharts() {
    if (!window.Chart?.instances) return;

    // Use requestAnimationFrame to optimize visual updates
    requestAnimationFrame(() => {
      for (let id in window.Chart.instances) {
        window.Chart.instances[id].resize();
      }
    });
  }

  // Function to initialize tooltips
  function initTooltips() {
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltips.length > 0 && typeof bootstrap !== 'undefined') {
      tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
      });
    }
  }

  // Function to show/hide loading indicator
  function showLoading(isLoading) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
      loadingIndicator.style.display = isLoading ? 'block' : 'none';
    }
  }

  // Optimized function to load dashboard data
  function loadDashboardData(endpoint, callback) {
    // Show loading indicator
    showLoading(true);

    // Check for cached data
    const cacheKey = `dashboard_data_${endpoint}`;
    const cachedData = sessionStorage.getItem(cacheKey);

    if (cachedData) {
      try {
        const data = JSON.parse(cachedData);
        if (callback && typeof callback === 'function') {
          // Use setTimeout to defer execution to next event loop
          setTimeout(() => callback(data), 0);
        }
        showLoading(false);
        return;
      } catch (e) {
        console.error('Error parsing cached dashboard data:', e);
      }
    }

    // Fetch data if not in cache
    fetch(endpoint)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        // Cache the response
        try {
          sessionStorage.setItem(cacheKey, JSON.stringify(data));
        } catch (e) {
          console.warn('Failed to cache dashboard data:', e);
        }

        if (callback && typeof callback === 'function') {
          callback(data);
        }
        showLoading(false);
      })
      .catch(error => {
        console.error('Error fetching dashboard data:', error);
        showLoading(false);
      });
  }

  // Default chart colors (moved inside the closure)
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

  // Default chart options for consistency (moved inside the closure)
  const defaultChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 400 // Reduced animation duration for better performance
    },
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

  // Helper functions for formatting
  window.formatDate = function(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, options);
  };

  window.formatNumber = function(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  };
})();
