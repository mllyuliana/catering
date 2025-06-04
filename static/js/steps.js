let currentStep = 1;
const totalSteps = 6;

function showStep(step) {
    console.log('Showing step:', step);
    // Скрываем все шаги
    document.querySelectorAll('.step-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // Показываем нужный шаг
    const stepContent = document.getElementById(`step${step}-content`);
    console.log('Step content element:', stepContent);
    if (stepContent) {
        stepContent.style.display = 'block';
    }
    
    // Обновляем текущий шаг
    currentStep = step;
    console.log('Current step updated to:', currentStep);
}

function nextStep() {
    console.log('Moving to next step from:', currentStep);
    if (currentStep < totalSteps) {
        showStep(currentStep + 1);
    }
}

function prevStep() {
    console.log('Moving to previous step from:', currentStep);
    if (currentStep > 1) {
        showStep(currentStep - 1);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded, showing step 1');
    showStep(1);
}); 