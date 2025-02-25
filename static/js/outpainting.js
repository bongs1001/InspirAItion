async function outpaintImage(imageUrl, prompt) {
    if (!imageUrl) {
        throw new Error('이미지 URL이 필요합니다.');
    }

    try {
        const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;
        const response = await fetch('/app/ai/outpaint/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: `image_url=${encodeURIComponent(imageUrl)}&prompt=${encodeURIComponent(prompt || '')}`
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '아웃페인팅 처리에 실패했습니다.');
        }

        return await response.json();
    } catch (error) {
        console.error('아웃페인팅 처리 중 오류 발생:', error);
        throw error;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const outpaintImageBtn = document.getElementById('outpaintImageBtn');
    
    if (outpaintImageBtn) {
        outpaintImageBtn.addEventListener('click', async function() {
            const imageUrl = document.getElementById('generatedImageUrl')?.value;
            const prompt = document.getElementById('promptInput')?.value;
            
            if (!imageUrl) {
                alert('먼저 이미지를 생성해주세요.');
                return;
            }
            
            const confirmMsg = '이미지 아웃페인팅을 진행하시겠습니까?\n(처리에 1~2분 정도 소요될 수 있습니다)';
            if (!confirm(confirmMsg)) {
                return;
            }
            
            try {
                outpaintImageBtn.disabled = true;
                document.getElementById('loadingModal').style.display = 'flex';
                document.getElementById('loadingText').textContent = 'ComfyUI로 이미지 아웃페인팅 중...';
                
                const result = await outpaintImage(imageUrl, prompt);
                
                if (result.image_url) {
                    const generatedImage = document.getElementById('generatedImage');
                    generatedImage.src = result.image_url;
                    document.getElementById('generatedImageUrl').value = result.image_url;
                    
                    generatedImage.style.display = 'block';
                    const noPreviewContent = document.getElementById('noPreviewContent');
                    if (noPreviewContent) {
                        noPreviewContent.style.display = 'none';
                    }
                    
                    alert('아웃페인팅 완료!\n이미지가 성공적으로 확장되었습니다.');
                } else {
                    throw new Error('아웃페인팅된 이미지 URL을 받지 못했습니다.');
                }
            } catch (error) {
                alert(`오류 발생: ${error.message}`);
                console.error('아웃페인팅 오류:', error);
            } finally {
                outpaintImageBtn.disabled = false;
                document.getElementById('loadingModal').style.display = 'none';
            }
        });
    }
});