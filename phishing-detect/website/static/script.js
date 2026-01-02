document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('urlInput');
    const checkBtn = document.getElementById('checkBtn');
    const resultArea = document.getElementById('resultArea');
    const resultText = document.getElementById('resultText');
    const resultDesc = document.getElementById('resultDesc');

    checkBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();

        if (!url) {
            alert('Mohon masukkan URL terlebih dahulu!');
            return;
        }

        // UI State: Loading
        checkBtn.classList.add('loading');
        checkBtn.disabled = true;
        resultArea.classList.add('hidden');

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url }),
            });

            const data = await response.json();

            // Reset UI
            checkBtn.classList.remove('loading');
            checkBtn.disabled = false;
            resultArea.classList.remove('hidden');

            if (data.error) {
                resultText.textContent = "Error";
                resultText.className = "phishing";
                resultDesc.textContent = data.error;
                return;
            }

            // Display Result
            if (data.result === 'Phishing') {
                resultText.textContent = "PHISHING DETECTED!";
                resultText.className = "phishing";
                resultDesc.textContent = "URL ini diprediksi berbahaya. Mohon jangan diklik atau bagikan informasi sensitif.";
            } else {
                resultText.textContent = "URL AMAN";
                resultText.className = "aman";
                resultDesc.textContent = "URL ini diprediksi aman untuk diakses.";
            }

        } catch (error) {
            checkBtn.classList.remove('loading');
            checkBtn.disabled = false;
            alert('Terjadi kesalahan koneksi. Silakan coba lagi.');
            console.error('Error:', error);
        }
    });

    // Enter key support
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            checkBtn.click();
        }
    });
});
