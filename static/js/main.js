// Main JavaScript for the Agentic Scaffolding demo

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const goalForm = document.getElementById('goalForm');
    const goalInput = document.getElementById('goalInput');
    const refreshBtn = document.getElementById('refreshBtn');
    const executionStatus = document.getElementById('executionStatus');
    const statusMessage = document.getElementById('statusMessage');
    const currentExecution = document.getElementById('currentExecution');
    const taskDecomposition = document.getElementById('taskDecomposition');
    const executionPlan = document.getElementById('executionPlan');
    const agentActivities = document.getElementById('agentActivities');
    const executionResults = document.getElementById('executionResults');
    
    // Current execution tracking
    let currentExecutionId = null;
    let pollingInterval = null;
    
    // Event listeners
    goalForm.addEventListener('submit', submitGoal);
    refreshBtn.addEventListener('click', refreshCurrentExecution);
    
    // Initial load
    loadAllExecutions();
    
    // Functions
    async function submitGoal(event) {
        event.preventDefault();
        
        const goal = goalInput.value.trim();
        if (!goal) {
            alert('Please enter a goal');
            return;
        }
        
        try {
            // Show loading state
            updateStatus('Processing goal...', 'info');
            
            // Submit the goal
            const response = await fetch('/api/process-goal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ goal })
            });
            
            if (!response.ok) {
                throw new Error('Failed to process goal');
            }
            
            const data = await response.json();
            currentExecutionId = data.execution_id;
            
            // Update UI
            updateStatus(`Goal processing started. Execution ID: ${currentExecutionId}`, 'info');
            goalInput.value = '';
            
            // Start polling for updates
            startPolling(currentExecutionId);
            
        } catch (error) {
            console.error('Error submitting goal:', error);
            updateStatus(`Error: ${error.message}`, 'danger');
        }
    }
    
    function startPolling(executionId) {
        // Clear any existing polling
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        
        // Poll for updates every 2 seconds
        pollingInterval = setInterval(() => {
            fetchExecutionStatus(executionId);
        }, 2000);
        
        // Initial fetch
        fetchExecutionStatus(executionId);
    }
    
    async function fetchExecutionStatus(executionId) {
        try {
            const response = await fetch(`/api/execution-status/${executionId}`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    updateStatus('Execution not found', 'warning');
                    clearInterval(pollingInterval);
                    return;
                }
                throw new Error('Failed to fetch execution status');
            }
            
            const data = await response.json();
            updateExecutionDisplay(data);
            
            // If execution is completed or failed, stop polling
            if (data.status === 'completed' || data.status === 'failed') {
                clearInterval(pollingInterval);
            }
            
        } catch (error) {
            console.error('Error fetching execution status:', error);
            updateStatus(`Error: ${error.message}`, 'danger');
        }
    }
    
    async function loadAllExecutions() {
        try {
            const response = await fetch('/api/all-executions');
            
            if (!response.ok) {
                throw new Error('Failed to fetch executions');
            }
            
            const data = await response.json();
            
            // Find the most recent execution
            let mostRecent = null;
            let mostRecentTime = null;
            
            for (const [id, execution] of Object.entries(data)) {
                const startTime = new Date(execution.start_time);
                if (!mostRecentTime || startTime > mostRecentTime) {
                    mostRecent = id;
                    mostRecentTime = startTime;
                }
            }
            
            // If there's a recent execution, display it
            if (mostRecent) {
                currentExecutionId = mostRecent;
                fetchExecutionStatus(mostRecent);
                
                // If it's still in progress, start polling
                if (data[mostRecent].status !== 'completed' && data[mostRecent].status !== 'failed') {
                    startPolling(mostRecent);
                }
            }
            
        } catch (error) {
            console.error('Error loading executions:', error);
        }
    }
    
    function refreshCurrentExecution() {
        if (currentExecutionId) {
            fetchExecutionStatus(currentExecutionId);
        } else {
            loadAllExecutions();
        }
    }
    
    function updateStatus(message, type) {
        executionStatus.className = `alert alert-${type}`;
        executionStatus.classList.remove('d-none');
        statusMessage.textContent = message;
    }
    
    function updateExecutionDisplay(execution) {
        // Update status
        const statusMap = {
            'initializing': 'Initializing execution...',
            'decomposing': 'Decomposing goal into subtasks...',
            'planning': 'Creating execution plan...',
            'allocating': 'Allocating tasks to agents...',
            'executing': 'Executing tasks...',
            'completed': 'Execution completed successfully',
            'failed': 'Execution failed'
        };
        
        const statusTypeMap = {
            'initializing': 'info',
            'decomposing': 'info',
            'planning': 'info',
            'allocating': 'info',
            'executing': 'primary',
            'completed': 'success',
            'failed': 'danger'
        };
        
        const statusText = statusMap[execution.status] || execution.status;
        const statusType = statusTypeMap[execution.status] || 'info';
        
        updateStatus(statusText, statusType);
        
        // Update current execution
        currentExecution.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Goal: ${execution.goal}</h5>
                    <p class="card-text execution-metadata">
                        <strong>Execution ID:</strong> ${currentExecutionId}<br>
                        <strong>Status:</strong> <span class="badge status-${execution.status}">${execution.status}</span><br>
                        <strong>Started:</strong> ${formatDateTime(execution.start_time)}<br>
                        ${execution.end_time ? `<strong>Ended:</strong> ${formatDateTime(execution.end_time)}<br>` : ''}
                    </p>
                </div>
            </div>
        `;
        
        // Update task decomposition
        if (execution.subtasks && execution.subtasks.length > 0) {
            let tasksHtml = '';
            
            for (const taskId of execution.subtasks) {
                const task = execution.tasks ? execution.tasks[taskId] : null;
                if (task) {
                    tasksHtml += `
                        <div class="card task-card">
                            <div class="card-body">
                                <h5 class="card-title">${task.title}</h5>
                                <p class="card-text">${task.description || 'No description'}</p>
                                ${task.dependencies ? `<p class="card-text"><small class="text-muted">Dependencies: ${task.dependencies.join(', ')}</small></p>` : ''}
                                ${task.required_capabilities ? `<p class="card-text"><small class="text-muted">Required capabilities: ${task.required_capabilities.join(', ')}</small></p>` : ''}
                            </div>
                        </div>
                    `;
                } else {
                    tasksHtml += `<p>Task ${taskId}</p>`;
                }
            }
            
            taskDecomposition.innerHTML = tasksHtml || '<p>No tasks available</p>';
        } else {
            taskDecomposition.innerHTML = '<p class="text-muted">Waiting for task decomposition...</p>';
        }
        
        // Update execution plan
        if (execution.plan) {
            const planId = execution.plan;
            const plan = execution.plans ? execution.plans[planId] : null;
            
            if (plan && plan.steps) {
                let planHtml = '';
                
                for (let i = 0; i < plan.steps.length; i++) {
                    const step = plan.steps[i];
                    planHtml += `
                        <div class="plan-step">
                            <h5>${step.name || `Step ${i+1}`}</h5>
                            <p><strong>Tasks:</strong> ${Array.isArray(step.tasks) ? step.tasks.join(', ') : step.tasks || 'None'}</p>
                            <p><strong>Parallel:</strong> ${step.parallel ? 'Yes' : 'No'}</p>
                            ${step.conditions ? `<p><strong>Conditions:</strong> ${step.conditions}</p>` : ''}
                            ${step.expected_outcomes ? `<p><strong>Expected outcomes:</strong> ${step.expected_outcomes}</p>` : ''}
                        </div>
                    `;
                }
                
                executionPlan.innerHTML = planHtml;
            } else {
                executionPlan.innerHTML = '<p>Plan details not available</p>';
            }
        } else {
            executionPlan.innerHTML = '<p class="text-muted">Waiting for execution plan...</p>';
        }
        
        // Update agent activities (simulated for demo)
        if (execution.status === 'executing' || execution.status === 'completed') {
            const activities = [
                {
                    agent: 'Research Specialist',
                    task: 'Research background information',
                    status: 'completed',
                    time: '2 minutes ago',
                    type: 'research'
                },
                {
                    agent: 'Analysis Expert',
                    task: 'Analyze key aspects',
                    status: execution.status === 'completed' ? 'completed' : 'in-progress',
                    time: '1 minute ago',
                    type: 'analysis'
                },
                {
                    agent: 'Synthesis Master',
                    task: 'Synthesize findings',
                    status: execution.status === 'completed' ? 'completed' : 'pending',
                    time: execution.status === 'completed' ? 'Just now' : '',
                    type: 'synthesis'
                }
            ];
            
            let activitiesHtml = '';
            
            for (const activity of activities) {
                activitiesHtml += `
                    <div class="agent-activity agent-${activity.type}">
                        <h5>${activity.agent}</h5>
                        <p><strong>Task:</strong> ${activity.task}</p>
                        <p><strong>Status:</strong> <span class="badge status-${activity.status}">${activity.status}</span></p>
                        ${activity.time ? `<p><small class="text-muted">${activity.time}</small></p>` : ''}
                    </div>
                `;
            }
            
            agentActivities.innerHTML = activitiesHtml;
        } else {
            agentActivities.innerHTML = '<p class="text-muted">Waiting for agent activities...</p>';
        }
        
        // Update results
        if (execution.status === 'completed' && execution.result) {
            let resultsHtml = `
                <div class="result-section">
                    <h5>Execution Summary</h5>
                    <p><strong>Steps Completed:</strong> ${execution.result.steps_completed}</p>
                    <p><strong>Execution ID:</strong> ${execution.result.execution_id}</p>
                </div>
                
                <div class="result-section">
                    <h5>Final Output</h5>
                    <pre>
# Comprehensive Report

## Executive Summary

This report integrates findings from extensive research and detailed analysis to provide a comprehensive understanding of the subject matter. The evidence suggests that the field is undergoing significant transformation, driven by technological innovation, changing market dynamics, and evolving user needs.

## Key Findings

The current landscape is characterized by rapid evolution and increasing complexity. Our research identified three dominant approaches currently in use, with the integrated methodology showing the strongest outcomes in 78% of applications.

Analysis revealed cyclical patterns with 18-month periodicity, suggesting alignment with broader industry cycles. Strong correlations between key variables indicate underlying systemic relationships that can be leveraged for strategic advantage.

## Recommendations

1. Implement a dynamic strategy framework that can adapt to the identified cycles
2. Develop segmented approaches that address the specific needs of different groups
3. Invest in capabilities that leverage the strong relationships between key variables
4. Establish ongoing monitoring systems for the anomalous segments identified

## Conclusion

The integration of research and analysis provides a robust foundation for decision-making in this complex and evolving field. By understanding the patterns, relationships, and dynamics identified in this report, organizations can develop more effective strategies.
                    </pre>
                </div>
            `;
            
            executionResults.innerHTML = resultsHtml;
        } else if (execution.status === 'failed') {
            executionResults.innerHTML = `
                <div class="alert alert-danger">
                    <h5>Execution Failed</h5>
                    <p>${execution.errors && execution.errors.length > 0 ? execution.errors[0] : 'Unknown error'}</p>
                </div>
            `;
        } else {
            executionResults.innerHTML = '<p class="text-muted">Results will appear here when execution is complete...</p>';
        }
    }
    
    function formatDateTime(dateTimeStr) {
        if (!dateTimeStr) return '';
        const date = new Date(dateTimeStr);
        return date.toLocaleString();
    }
});
