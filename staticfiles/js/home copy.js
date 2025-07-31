// static/js/home.js

document.addEventListener('DOMContentLoaded', () => {
    const executeQueryBtn = document.getElementById('executeQueryBtn');
    const nextButton = document.getElementById('nextButton');
    const toggleAtomicChecksBtn = document.getElementById('toggleAtomicChecksBtn');
    const atomicChecksContainer = document.getElementById('atomicChecksContainer');
    const atomicChecksList = document.getElementById('atomicChecksList');
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
            const mainQueryResultPre = document.getElementById('mainQueryResult');
            const chartContainer = document.getElementById('chartContainer');

            // Reset UI for new query
            resultContainer.classList.remove('hidden');
            mainQueryResultPre.textContent = 'Loading...';
            nextButton.classList.add('hidden'); // Hide chart button initially
            chartContainer.classList.add('hidden'); // Hide chart container initially
            atomicChecksContainer.classList.add('hidden'); // Hide atomic checks
            atomicChecksList.innerHTML = ''; // Clear previous atomic checks
            toggleAtomicChecksBtn.textContent = 'Show Atomic Checks'; // Reset button text

            // Destroy existing chart if it exists and clear the canvas
            if (myChart) {
                myChart.destroy();
                myChart = null;
            }
            // Ensure the canvas is cleared even if Chart.js instance was not found/destroyed
            const chartCanvas = document.getElementById('pieChart');
            if (chartCanvas) {
                const ctx = chartCanvas.getContext('2d');
                ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
            }

            // Disable buttons during fetch
            executeQueryBtn.disabled = true;
            executeQueryBtn.textContent = 'Executing...';
            nextButton.disabled = true;
            toggleAtomicChecksBtn.disabled = true;


            // AJAX POST for generating SQL
            fetch('/api/generate_sql/', {
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
                        showCustomToast(data.message || 'SQL Generated', 'success'); // showCustomToast comes from utils.js
                        // *** IMPORTANT CHANGE HERE: Directly use data.data, it's already an object ***
                        if (data.data && typeof data.data === 'object') {
                            const responseData = data.data; // Renamed for clarity, it's the inner 'data' object

                            // Display Main Query
                            if (typeof responseData.main_query === 'string') {
                                mainQueryResultPre.textContent = responseData.main_query;
                                nextButton.classList.remove('hidden'); // Show the "Generate Chart" button
                                nextButton.disabled = false; // Enable the "Generate Chart" button
                                nextButton.dataset.sqlQuery = responseData.main_query; // Store SQL query for chart generation
                            } else {
                                mainQueryResultPre.textContent = 'No main SQL query returned.';
                                nextButton.classList.add('hidden');
                            }

                            // Display Atomic Checks
                            if (Array.isArray(responseData.atomic_checks) && responseData.atomic_checks.length > 0) {
                                toggleAtomicChecksBtn.disabled = false;
                                responseData.atomic_checks.forEach((check, index) => {
                                    const checkItem = document.createElement('div');
                                    checkItem.classList.add('mb-3', 'p-3', 'border', 'border-gray-300', 'rounded-md', 'bg-gray-50');
                                    checkItem.innerHTML = `
                                        <p class="font-medium text-gray-800 mb-1">${index + 1}. ${check.description}</p>
                                        <pre class="bg-gray-100 p-2 rounded-md text-gray-700 overflow-auto text-xs font-mono mb-2">${check.query}</pre>
                                        <button class="test-atomic-query-btn bg-purple-600 hover:bg-purple-700 text-white text-sm py-1 px-3 rounded-md shadow-sm" data-query="${encodeURIComponent(check.query)}">Test This Query</button>
                                        <pre class="atomic-query-result bg-yellow-50 p-2 rounded-md text-yellow-800 overflow-auto text-xs font-mono mt-2 hidden">Result will appear here...</pre>
                                    `;
                                    atomicChecksList.appendChild(checkItem);
                                });

                                // Attach event listeners to the new "Test This Query" buttons
                                document.querySelectorAll('.test-atomic-query-btn').forEach(button => {
                                    button.addEventListener('click', function () {
                                        const queryToTest = decodeURIComponent(this.dataset.query);
                                        const resultPre = this.nextElementSibling; // The pre tag right after the button

                                        resultPre.textContent = 'Executing atomic query...';
                                        resultPre.classList.remove('hidden');
                                        this.disabled = true;

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
                                                    resultPre.textContent = 'Success: ' + (data.message || 'Executed atomic query successfully');
                                                    resultPre.classList.remove('text-yellow-800');
                                                    resultPre.classList.remove('bg-yellow-50');
                                                    resultPre.classList.add('text-green-800');
                                                    resultPre.classList.add('bg-green-50');
                                                    showCustomToast('Atomic check successful!', 'success');
                                                } else {
                                                    resultPre.textContent = 'Error: ' + (data.message || 'Failed to execute atomic query');
                                                    resultPre.classList.remove('text-green-800');
                                                    resultPre.classList.remove('bg-green-50');
                                                    resultPre.classList.add('text-red-800');
                                                    resultPre.classList.add('bg-red-50');
                                                    showCustomToast(data.message || 'Atomic check failed!', 'error');
                                                }
                                            })
                                            .catch(error => {
                                                console.error('Error testing atomic query:', error);
                                                resultPre.textContent = 'Network error during atomic query test.';
                                                resultPre.classList.remove('text-green-800');
                                                resultPre.classList.remove('bg-green-50');
                                                resultPre.classList.add('text-red-800');
                                                resultPre.classList.add('bg-red-50');
                                                showCustomToast('Network error during atomic check.', 'error');
                                            })
                                            .finally(() => {
                                                this.disabled = false;
                                            });
                                    });
                                });

                            } else {
                                toggleAtomicChecksBtn.disabled = true;
                                atomicChecksList.innerHTML = '<p class="text-gray-600">No atomic checks generated for this query.</p>';
                            }

                        } else {
                            mainQueryResultPre.textContent = 'No data returned or data format is incorrect.';
                            nextButton.classList.add('hidden');
                            toggleAtomicChecksBtn.disabled = true;
                        }
                    } else {
                        showCustomToast(data.message || 'Something went wrong during SQL generation', 'error');
                        mainQueryResultPre.textContent = 'Error: ' + (data.message || 'Unknown error');
                        nextButton.classList.add('hidden');
                        toggleAtomicChecksBtn.disabled = true;
                    }
                })
                .catch((error) => {
                    console.error('Error:', error);
                    showCustomToast('Network error during SQL generation. Please try again.', 'error');
                    mainQueryResultPre.textContent = 'Network error. Please try again.';
                    nextButton.classList.add('hidden');
                    toggleAtomicChecksBtn.disabled = true;
                })
                .finally(() => {
                    // Re-enable the execute query button
                    executeQueryBtn.disabled = false;
                    executeQueryBtn.textContent = 'Execute Query';
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
            const sqlQuery = this.dataset.sqlQuery; // Retrieve SQL query from dataset

            if (!sqlQuery) {
                showCustomToast('No SQL query available to generate chart.', 'error');
                return;
            }

            // Show chart loading indicator
            const chartContainer = document.getElementById('chartContainer');
            chartContainer.classList.remove('hidden');

            // IMPORTANT: Recreate the canvas element to ensure a clean slate
            const oldCanvas = document.getElementById('pieChart');
            const parentDiv = oldCanvas ? oldCanvas.parentNode : null;

            if (parentDiv) {
                parentDiv.removeChild(oldCanvas);
            }

            const newCanvas = document.createElement('canvas');
            newCanvas.id = 'pieChart';
            newCanvas.width = 300; // Set initial width
            newCanvas.height = 300; // Set initial height
            if (parentDiv) {
                parentDiv.appendChild(newCanvas);
            } else {
                // Fallback if parentDiv is null (e.g., chartContainer not fully rendered)
                chartContainer.appendChild(newCanvas);
            }

            const ctx = newCanvas.getContext('2d');

            // Destroy existing chart if it exists (though recreating canvas largely avoids this)
            if (myChart) {
                myChart.destroy();
                myChart = null;
            }

            // Disable button during chart generation
            nextButton.disabled = true;
            nextButton.textContent = 'Generating Chart...';

            // AJAX POST request for chart data
            fetch('/api/generate_chart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(), // getCSRFToken comes from utils.js
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

                        // Initialize Chart.js on the NEW canvas
                        myChart = new Chart(ctx, {
                            type: 'pie',
                            data: {
                                labels: data.data.chart_data.labels,
                                datasets: [
                                    {
                                        data: data.data.chart_data.values,
                                        backgroundColor: [
                                            '#4e79a7',
                                            '#f28e2b',
                                            '#e15759',
                                            '#76b7b2',
                                            '#59a14f',
                                            '#edc949',
                                            '#af7aa1',
                                            '#ff9da7',
                                            '#9c755f',
                                            '#bab0ab',
                                        ],
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
                            },
                        });
                    } else {
                        showCustomToast(
                            data.message || 'No chart data received or error during chart generation',
                            'error'
                        );
                        // Display error message on the new canvas
                        ctx.clearRect(0, 0, newCanvas.width, newCanvas.height);
                        ctx.font = '16px Inter';
                        ctx.fillStyle = '#ef4444';
                        ctx.textAlign = 'center';
                        ctx.fillText(
                            data.message || 'No chart data available',
                            newCanvas.width / 2,
                            newCanvas.height / 2
                        );
                    }
                })
                .catch((error) => {
                    console.error('Error:', error);
                    showCustomToast('Network error during chart generation. Please try again.', 'error');
                    // Display network error on the new canvas
                    ctx.clearRect(0, 0, newCanvas.width, newCanvas.height);
                    ctx.font = '16px Inter';
                    ctx.fillStyle = '#ef4444';
                    ctx.textAlign = 'center';
                    ctx.fillText('Network error.', newCanvas.width / 2, newCanvas.height / 2);
                })
                .finally(() => {
                    nextButton.disabled = false;
                    nextButton.textContent = 'Generate Chart';
                });
        });
    }
});