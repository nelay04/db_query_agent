// static/js/home.js

document.addEventListener('DOMContentLoaded', () => {
    const executeQueryBtn = document.getElementById('executeQueryBtn');
    const nextButton = document.getElementById('nextButton'); // This will become "Execute query and Generate chart"
    const toggleAtomicChecksBtn = document.getElementById('toggleAtomicChecksBtn');
    const atomicChecksContainer = document.getElementById('atomicChecksContainer');
    const atomicChecksList = document.getElementById('atomicChecksList');
    const mainQueryResultPre = document.getElementById('mainQueryResult'); // The answer field for ratio-like result
    
    // New elements for chart display section
    const chartDisplaySection = document.getElementById('chartDisplaySection');
    const chartTypeSelect = document.getElementById('chartTypeSelect');
    const chartQueryResultPre = document.getElementById('chartQueryResult'); // To display the 'result' from chart API
    const chartCanvas = document.getElementById('mainChart');
    const chartContainer = document.getElementById('chartContainer');

    let myChart = null; // Variable to hold the Chart.js instance, scoped to home.js

    const queryForm = document.getElementById('queryForm');
    if (queryForm) {
        queryForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const form = e.target;
            const userQueryInput = form.userQuery;
            const formData = {
                user_query: userQueryInput.value,
            };

            const resultContainer = document.getElementById('queryResultContainer');


            // Reset UI for new query
            resultContainer.classList.remove('hidden');
            mainQueryResultPre.textContent = 'Loading...'; // Clear previous result
            nextButton.classList.add('hidden'); // Hide "Execute query and Generate chart" button initially
            chartDisplaySection.classList.add('hidden'); // Hide chart display section initially
            chartQueryResultPre.textContent = 'Loading Chart Data Result...'; // Clear previous chart query result
            atomicChecksContainer.classList.add('hidden'); // Hide atomic checks
            atomicChecksList.innerHTML = ''; // Clear previous atomic checks
            toggleAtomicChecksBtn.textContent = 'Show Atomic Checks'; // Reset button text
            toggleAtomicChecksBtn.classList.add('hidden'); // Hide "Show Atomic Checks" button

            // Destroy existing chart if it exists and clear the canvas
            if (myChart) {
                myChart.destroy();
                myChart = null;
            }
            // Ensure the canvas is cleared even if Chart.js instance was not found/destroyed
            if (chartCanvas) {
                const ctx = chartCanvas.getContext('2d');
                ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
            }

            // Disable buttons during fetch
            executeQueryBtn.disabled = true;
            executeQueryBtn.textContent = 'Running Query...'; // Changed text
            nextButton.disabled = true;
            toggleAtomicChecksBtn.disabled = true;


            // AJAX POST for generating SQL and getting initial result
            fetch('/api/gather_information/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(), // getCSRFToken comes from utils.js
                },
                body: JSON.stringify(formData),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        showCustomToast(data.message || 'Data Retrieved', 'success'); // Toast for data retrieval
                        if (data.data && typeof data.data === 'object') {
                            const responseData = data.data;

                            // Display Main Query Result (the ratio-like answer)
                            if (responseData.result && typeof responseData.result.main_query === 'string') {
                                mainQueryResultPre.textContent = responseData.result.main_query; // Display the direct answer
                                // We now set the SQL query for the 'Execute query and Generate chart' button here if needed for the chart API
                                nextButton.dataset.sqlQuery = responseData.result.main_query;
                                nextButton.classList.remove('hidden'); // Show the "Execute query and Generate chart" button
                                nextButton.disabled = false; // Enable the "Execute query and Generate chart" button
                                nextButton.textContent = 'Execute query and Generate chart'; // Ensure button text is correct
                            } else {
                                mainQueryResultPre.textContent = 'No main result returned.';
                                nextButton.classList.add('hidden');
                            }

                            // Display Atomic Checks (discovery_data)
                            if (Array.isArray(responseData.discovery_data) && responseData.discovery_data.length > 0) {
                                toggleAtomicChecksBtn.disabled = false;
                                toggleAtomicChecksBtn.classList.remove('hidden'); // Show button on success with data
                                responseData.discovery_data.forEach((check, index) => {
                                    const checkItem = document.createElement('div');
                                    checkItem.classList.add('mb-3', 'p-3', 'border', 'border-gray-300', 'rounded-md', 'bg-gray-50');

                                    let resultDisplay = '';
                                    if (check.query_result && check.query_result.length > 0) {
                                        resultDisplay = JSON.stringify(check.query_result, null, 2);
                                    } else {
                                        resultDisplay = 'No result returned or result is empty.';
                                    }

                                    checkItem.innerHTML = `
                                        <p class="font-medium text-gray-800 mb-1">${index + 1}. ${check.description}</p>
                                        <h6 class="text-sm font-medium text-gray-700 mb-1">Query:</h6>
                                        <pre class="bg-gray-100 p-2 rounded-md text-gray-700 overflow-auto text-xs font-mono mb-2">${check.query}</pre>
                                        <h6 class="text-sm font-medium text-gray-700 mb-1">Result:</h6>
                                        ${
                                            resultDisplay === 'No result returned or result is empty.'
                                                ? `<pre class="bg-yellow-50 p-2 rounded-md text-yellow-800 overflow-auto text-xs font-mono mt-2">${resultDisplay}</pre>`
                                                : `<pre class="bg-green-100 p-2 rounded-md text-green-800 overflow-auto text-xs font-mono mt-2">${resultDisplay}</pre>`
                                        }
                                    `;
                                    atomicChecksList.appendChild(checkItem);
                                });
                            } else {
                                toggleAtomicChecksBtn.disabled = true;
                                toggleAtomicChecksBtn.classList.add('hidden'); // Ensure hidden if no data
                                atomicChecksList.innerHTML = '<p class="text-gray-600">No atomic checks generated for this query.</p>';
                            }

                        } else {
                            mainQueryResultPre.textContent = 'No data returned or data format is incorrect.';
                            nextButton.classList.add('hidden');
                            toggleAtomicChecksBtn.disabled = true;
                            toggleAtomicChecksBtn.classList.add('hidden'); // Ensure hidden if no data
                        }
                    } else {
                        showCustomToast(data.message || 'Something went wrong during query execution', 'error');
                        mainQueryResultPre.textContent = 'Error: ' + (data.message || 'Unknown error');
                        nextButton.classList.add('hidden');
                        toggleAtomicChecksBtn.disabled = true;
                        toggleAtomicChecksBtn.classList.add('hidden'); // Ensure hidden on error
                    }
                })
                .catch((error) => {
                    console.error('Error:', error);
                    showCustomToast('Network error during query execution. Please try again.', 'error');
                    mainQueryResultPre.textContent = 'Network error. Please try again.';
                    nextButton.classList.add('hidden');
                    toggleAtomicChecksBtn.disabled = true;
                    toggleAtomicChecksBtn.classList.add('hidden'); // Ensure hidden on network error
                })
                .finally(() => {
                    executeQueryBtn.disabled = false;
                    executeQueryBtn.textContent = 'Run the Query'; // Changed back to "Run the Query"
                });
        });
    }

    // Toggle Atomic Checks Visibility
    if (toggleAtomicChecksBtn) {
        toggleAtomicChecksBtn.addEventListener('click', () => {
            if (atomicChecksContainer.classList.contains('hidden')) {
                atomicChecksContainer.classList.remove('hidden');
                toggleAtomicChecksBtn.textContent = 'Hide Atomic Checks';
            } else {
                atomicChecksContainer.classList.add('hidden');
                toggleAtomicChecksBtn.textContent = 'Show Atomic Checks';
            }
        });
    }

    // Attach the event listener for nextButton (Execute query and Generate chart)
    if (nextButton) {
        nextButton.addEventListener('click', function () {
            const sqlQuery = this.dataset.sqlQuery; // Get the SQL query stored from the previous step
            const selectedChartType = chartTypeSelect.value; // Get the selected chart type

            if (!sqlQuery) {
                showCustomToast('No SQL query available to generate chart.', 'error');
                return;
            }

            chartDisplaySection.classList.remove('hidden'); // Show the chart display section
            chartQueryResultPre.textContent = 'Loading Chart Data Result...'; // Reset text

            // Destroy existing chart if it exists and clear the canvas
            if (myChart) {
                myChart.destroy();
                myChart = null;
            }
            // Recreate canvas element to ensure a clean slate for Chart.js
            const oldCanvas = document.getElementById('mainChart');
            const parentDiv = oldCanvas ? oldCanvas.parentNode : chartContainer; // Use chartContainer if oldCanvas not found

            if (oldCanvas && parentDiv) {
                parentDiv.removeChild(oldCanvas);
            }

            const newCanvas = document.createElement('canvas');
            newCanvas.id = 'mainChart';
            newCanvas.width = 300;
            newCanvas.height = 300;
            if (parentDiv) {
                parentDiv.appendChild(newCanvas);
            } else {
                chartContainer.appendChild(newCanvas); // Fallback, though parentDiv should be chartContainer
            }
            const ctx = newCanvas.getContext('2d');


            nextButton.disabled = true;
            nextButton.textContent = 'Generating Chart...';

            // AJAX POST for generating Chart
            fetch('/api/generate_chart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify({ sql_query: sqlQuery }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (
                        data.success &&
                        data.data &&
                        data.data.chart_data &&
                        data.data.chart_data.labels &&
                        data.data.chart_data.values
                    ) {
                        showCustomToast(data.message || 'Chart Generated Successfully', 'success');

                        // Display the result array in chartQueryResultPre
                        if (data.data.result) {
                            chartQueryResultPre.textContent = JSON.stringify(data.data.result, null, 2);
                        } else {
                            chartQueryResultPre.textContent = 'No explicit query result for chart.';
                        }

                        myChart = new Chart(ctx, {
                            type: selectedChartType, // Use the selected chart type
                            data: {
                                labels: data.data.chart_data.labels,
                                datasets: [
                                    {
                                        data: data.data.chart_data.values,
                                        backgroundColor: [
                                            '#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f',
                                            '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab',
                                        ],
                                        // Add border for better visibility on some charts
                                        borderColor: '#ffffff', 
                                        borderWidth: 1,
                                    },
                                ],
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        position: 'bottom',
                                        labels: {
                                            boxWidth: 10,
                                        },
                                    },
                                },
                                // Specific options for different chart types
                                ...(selectedChartType === 'pie' || selectedChartType === 'doughnut' ? {} : {
                                    scales: {
                                        y: {
                                            beginAtZero: true
                                        }
                                    }
                                })
                            },
                        });
                    } else {
                        showCustomToast(
                            data.message || 'No chart data received or error during chart generation',
                            'error'
                        );
                        ctx.clearRect(0, 0, newCanvas.width, newCanvas.height);
                        ctx.font = '16px Inter';
                        ctx.fillStyle = '#ef4444';
                        ctx.textAlign = 'center';
                        ctx.fillText(
                            data.message || 'No chart data available',
                            newCanvas.width / 2,
                            newCanvas.height / 2
                        );
                        chartQueryResultPre.textContent = 'Error: ' + (data.message || 'No chart data available');
                    }
                })
                .catch((error) => {
                    console.error('Error:', error);
                    showCustomToast('Network error during chart generation. Please try again.', 'error');
                    ctx.clearRect(0, 0, newCanvas.width, newCanvas.height);
                    ctx.font = '16px Inter';
                    ctx.fillStyle = '#ef4444';
                    ctx.textAlign = 'center';
                    ctx.fillText('Network error.', newCanvas.width / 2, newCanvas.height / 2);
                    chartQueryResultPre.textContent = 'Network error. Please try again.';
                })
                .finally(() => {
                    nextButton.disabled = false;
                    nextButton.textContent = 'Execute query and Generate chart';
                });
        });
    }

    // Add event listener for chart type selection change
    if (chartTypeSelect) {
        chartTypeSelect.addEventListener('change', () => {
            // Trigger chart regeneration with the new type if data is already loaded
            if (myChart && nextButton.dataset.sqlQuery) {
                nextButton.click(); // Simulate a click on the "Generate Chart" button
            }
        });
    }
});