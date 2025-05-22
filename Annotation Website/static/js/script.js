let annotatedCount = parseInt(document.getElementById('progress-count').textContent);
let totalSentences = parseInt(document.getElementById('progress-bar-container').getAttribute('data-total-sentences'));

document.addEventListener('DOMContentLoaded', function() {
    const progressBarContainer = document.getElementById('progress-bar-container');
    if (progressBarContainer) {
        updateProgress();
    }
});

function annotate(button, sentiment) {
    const sentenceBox = button.closest('.sentence-box');
    const sentence = sentenceBox.querySelector('.sentence').textContent;
    
    fetch('api_annotate.php', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sentence, sentiment }),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
        annotatedCount++;
        updateProgress();
        
        // Disable buttons for the annotated sentence
        sentenceBox.querySelectorAll('button').forEach(btn => btn.disabled = true);
        sentenceBox.classList.add('annotated');
        
        // If all sentences are annotated, reload the page
        if (annotatedCount === totalSentences) {
            setTimeout(() => location.reload(), 1000);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function updateProgress() {
    const progressCount = document.getElementById('progress-count');
    const progressBar = document.querySelector('[role="progressbar"] > div');
    
    if (progressCount && progressBar) {
        progressCount.textContent = annotatedCount;
        const percentage = (annotatedCount / totalSentences) * 100;
        progressBar.style.width = `${percentage}%`;
        progressBar.parentElement.setAttribute('aria-valuenow', percentage);
    }
}