// static/js/charts.js

document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('attendanceChart');
    if (!canvas) {
        console.warn('Canvas element #attendanceChart not found');
        return;
    }

    // Get data from data-* attributes
    let dates = [];
    let present = [];

    try {
        dates = JSON.parse(canvas.dataset.dates || '[]');
        present = JSON.parse(canvas.dataset.present || '[]');
    } catch (err) {
        console.error('Failed to parse chart data from data attributes:', err);
        return;
    }

    // Safety check
    if (!Array.isArray(dates) || !Array.isArray(present) || dates.length === 0) {
        console.warn('No valid attendance data available for chart');
        return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.error('Cannot get 2D context from canvas');
        return;
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Present Days',
                data: present,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.12)',
                borderWidth: 3,
                tension: 0.35,
                fill: true,
                pointBackgroundColor: '#0d6efd',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    ticks: {
                        stepSize: 1,
                        callback: function(value) {
                            return value === 1 ? 'Present' : 'Absent';
                        },
                        font: { size: 12 }
                    },
                    grid: { color: 'rgba(0,0,0,0.08)' }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 12 } },
                    title: {
                        display: true,
                        text: 'Date',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { font: { size: 14 } }
                },
                title: {
                    display: true,
                    text: 'Your Attendance Trend Over Time',
                    font: { size: 18, weight: 'bold' },
                    padding: { top: 10, bottom: 20 }
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleFont: { size: 14 },
                    bodyFont: { size: 13 },
                    padding: 12
                }
            }
        }
    });
});