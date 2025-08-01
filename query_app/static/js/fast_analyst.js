// static/js/home.js

document.addEventListener('DOMContentLoaded', () => {
    const executeQueryBtn = document.getElementById('executeQueryBtn');
    const nextButton = document.getElementById('nextButton');
    const toggleAtomicChecksBtn = document.getElementById('toggleAtomicChecksBtn');
    const atomicChecksContainer = document.getElementById('atomicChecksContainer');
    const atomicChecksList = document.getElementById('atomicChecksList');
    const mainQueryResultPre = document.getElementById('mainQueryResult'); // The answer field for ratio-like result
    
    // New elements for chart display section
    const chartDisplaySection = document.getElementById('chartDisplaySection');
    const chartTypeSelect = document.getElementById('chartTypeSelect');
    const chartQueryResultPre = document.getElementById('chartQueryResult'); // To display the 'result' from chart API
    const chartCanvas = document.getElementById('mainChart'); // Renamed from pieChart to mainChart
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
            nextButton.classList.add('hidden'); // Hide "Generate Chart" button initially
            chartDisplaySection.classList.add('hidden'); // Hide chart display section initially
            chartQueryResultPre.textContent = 'Loading Chart Data Result...'; // Clear previous chart query result
            atomicChecksContainer.classList.add('hidden'); // Hide atomic checks container
            atomicChecksList.innerHTML = ''; // Clear previous atomic checks
            toggleAtomicChecksBtn.textContent = 'Show Atomic Checks'; // Reset button text
            toggleAtomicChecksBtn.classList.add('hidden'); // Ensure "Show Atomic Checks" button is hidden initially


            // Destroy existing chart if it exists and clear the canvas
            if (myChart) {
                myChart.destroy();
                myChart = null;
            }
            // Ensure the canvas is cleared even if Chart.js instance was not found/destroyed
            // Note: The HTML refers to 'mainChart' now
            const currentChartCanvas = document.getElementById('mainChart');
            if (currentChartCanvas) {
                const ctx = currentChartCanvas.getContext('2d');
                ctx.clearRect(0, 0, currentChartCanvas.width, currentChartCanvas.height);
            }

            // Disable buttons during fetch
            executeQueryBtn.disabled = true;
            executeQueryBtn.textContent = 'Running Query...'; // Changed text
            nextButton.disabled = true;
            toggleAtomicChecksBtn.disabled = true; // Keep disabled until atomic checks are available


            // AJAX POST for generating SQL and getting initial result
            fetch('/api/generate_sql/', { // Changed API endpoint to generate_sql
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
                        showCustomToast(data.message || 'SQL Generated Successfully', 'success'); // Toast for data retrieval
                        if (data.data && typeof data.data === 'object') {
                            const responseData = data.data;

                            // Display Main Query Result (the ratio-like answer)
                            if (responseData.main_query && typeof responseData.main_query === 'string') {
                                mainQueryResultPre.textContent = responseData.main_query; // Display the direct answer (SQL Query)
                                // We now set the SQL query for the 'Generate Chart' button here
                                nextButton.dataset.sqlQuery = responseData.main_query;
                                nextButton.classList.remove('hidden'); // Show the "Generate Chart" button
                                nextButton.disabled = false; // Enable the "Generate Chart" button
                                nextButton.textContent = 'Generate Chart'; // Ensure button text is correct
                            } else {
                                mainQueryResultPre.textContent = 'No main SQL query returned.';
                                nextButton.classList.add('hidden');
                            }

                            // Display Atomic Checks
                            // Only show toggleAtomicChecksBtn if there is actual atomic_checks data
                            if (Array.isArray(responseData.atomic_checks) && responseData.atomic_checks.length > 0) {
                                toggleAtomicChecksBtn.disabled = false;
                                toggleAtomicChecksBtn.classList.remove('hidden'); // Show button on success with data
                                responseData.atomic_checks.forEach((check, index) => {
                                    const checkItem = document.createElement('div');
                                    checkItem.classList.add('mb-3', 'p-3', 'border', 'border-gray-300', 'rounded-md', 'bg-gray-50');

                                    // Placeholder for result display, will be populated when "Test This Query" is clicked
                                    checkItem.innerHTML = `
                                        <p class="font-medium text-gray-800 mb-1">${index + 1}. ${check.description}</p>
                                        <h6 class="text-sm font-medium text-gray-700 mb-1">Query:</h6>
                                        <pre class="bg-gray-100 p-2 rounded-md text-gray-700 overflow-auto text-xs font-mono mb-2">${check.query}</pre>
                                        <button class="test-atomic-query-btn w-full bg-indigo-500 hover:bg-indigo-600 text-white font-medium py-1 px-3 rounded-md shadow-sm text-sm mt-2" data-query="${encodeURIComponent(check.query)}">Test This Query</button>
                                        <pre class="atomic-query-result bg-gray-50 p-2 rounded-md overflow-auto text-xs font-mono mt-2 hidden"></pre>
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

    // Attach the event listener for nextButton (Generate Chart)
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
            newCanvas.id = 'mainChart'; // Ensure ID matches HTML
            newCanvas.width = 300;
            newCanvas.height = 300;
            if (parentDiv) {
                parentDiv.appendChild(newCanvas);
            } else {
                chartContainer.appendChild(newCanvas); // Fallback
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
                                ...(selectedChartType === 'pie' || selectedChartType === 'doughnut' || selectedChartType === 'polarArea' ? {} : {
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
                    nextButton.textContent = 'Generate Chart';
                });
        });
    }

    // Add event listener for chart type selection change
    if (chartTypeSelect) {
        chartTypeSelect.addEventListener('change', () => {
            // Trigger chart regeneration with the new type if data is already loaded
            if (myChart && nextButton.dataset.sqlQuery) {
                // Since the chart display is tied to nextButton click, we simulate it.
                // This will refetch data if necessary, or just redraw with new type if data is in cache.
                // Assuming /api/generate_chart/ always returns the data, not just chart config.
                nextButton.click(); // Simulate a click on the "Generate Chart" button
            }
        });
    }

    // IMPORTANT: The "Test This Query" button logic from your previous home.js.
    // Ensure you have an API endpoint '/api/check-atomic-query/' to handle this.
    // If not, this part will need to be adjusted or the buttons will not work.
    // This part should be placed outside the queryForm submit listener to avoid re-attaching multiple times.
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('test-atomic-query-btn')) {
            const button = event.target;
            const queryToTest = decodeURIComponent(button.dataset.query);
            const resultPre = button.nextElementSibling; // The pre tag right after the button

            resultPre.textContent = 'Executing atomic query...';
            resultPre.classList.remove('hidden');
            button.disabled = true;

            fetch('/api/check-atomic-query/', { // New API endpoint for atomic checks
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify({ query: queryToTest }),
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Typing effect for result display
                        let displayResult = '';
                        if (data.data && data.data.result) {
                            displayResult = JSON.stringify(data.data.result, null, 2);
                        } else {
                            displayResult = 'No result.';
                        }
                        resultPre.textContent = 'Success: ' + displayResult;
                        resultPre.classList.remove('text-yellow-800', 'bg-yellow-50', 'text-red-800', 'bg-red-50');
                        resultPre.classList.add('text-green-800', 'bg-green-50');
                        showCustomToast('Atomic check successful!', 'success');
                    } else {
                        resultPre.textContent = 'Error: ' + (data.message || 'Failed to execute atomic query');
                        resultPre.classList.remove('text-green-800', 'bg-green-50', 'text-yellow-800', 'bg-yellow-50');
                        resultPre.classList.add('text-red-800', 'bg-red-50');
                        showCustomToast(data.message || 'Atomic check failed!', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error testing atomic query:', error);
                    resultPre.textContent = 'Network error during atomic query test.';
                    resultPre.classList.remove('text-green-800', 'bg-green-50', 'text-yellow-800', 'bg-yellow-50');
                    resultPre.classList.add('text-red-800', 'bg-red-50');
                    showCustomToast('Network error during atomic check.', 'error');
                })
                .finally(() => {
                    button.disabled = false;
                });
        }
    });

});