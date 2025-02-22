document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.querySelector('[name="prompt"]');
    const generateBtn = document.getElementById("generateImageBtn");
    const voiceInputBtn = document.getElementById("voiceInputBtn");
    const aiVoiceInputBtn = document.getElementById("aiVoiceInputBtn");
    const speechModal = document.getElementById("speechRecognitionModal");
    const aiProcessingModal = document.getElementById("aiProcessingModal");

    // Initialize URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const imageUrl = urlParams.get("image_url");
    const generatedPrompt = urlParams.get("generated_prompt");
    const originalPrompt = urlParams.get("original_prompt");

    if (imageUrl && generatedPrompt) {
        document.getElementById("imagePreview").style.display = "block";
        document.getElementById("generatedImage").src = imageUrl;
        document.getElementById("generatedImageUrl").value = imageUrl;
        document.getElementById("generatedPrompt").value = generatedPrompt;

        if (searchInput) {
            searchInput.value = originalPrompt || "";
        }
    }

    function showModal(modal) {
        if (modal) {
            modal.style.display = "flex";
            modal.style.justifyContent = "center";
            modal.style.alignItems = "center";
            // 모달이 완전히 표시되도록 약간의 지연 추가
            setTimeout(() => {
                modal.style.opacity = "1";
            }, 10);
        }
    }

    function hideModal(modal) {
        if (modal) {
            modal.style.opacity = "0";
            // fade out 효과를 위한 지연 후 display none 처리
            setTimeout(() => {
                modal.style.display = "none";
            }, 300);
        }
    }

    // 마지막 포커스된 입력 요소를 추적하는 변수
    let lastFocusedInput = null;

    // 모든 입력 필드에 대해 포커스 이벤트 리스너 추가
    document.querySelectorAll('input[type="text"], textarea').forEach((input) => {
        input.addEventListener("focus", () => {
            lastFocusedInput = input;
        });
    });

    function handleVoiceInput(useAI = false, user_style) {
        if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
            alert("이 브라우저는 음성 인식을 지원하지 않습니다.");
            return;
        }

        // 입력 가능한 모든 필드 조회
        const inputFields = Array.from(document.querySelectorAll('input[type="text"], textarea')).filter(input => 
            !input.readOnly && !input.disabled && input.style.display !== 'none'
        );

        // 타겟 입력 필드 선택 (마지막 포커스 필드 또는 첫 번째 편집 가능한 필드)
        const targetInput = lastFocusedInput && !lastFocusedInput.readOnly && !lastFocusedInput.disabled
            ? lastFocusedInput
            : inputFields[0];

        if (!targetInput) {
            console.error("음성 입력을 처리할 수 있는 입력 필드를 찾을 수 없습니다.");
            alert("음성 입력을 처리할 수 있는 입력 필드를 찾을 수 없습니다.");
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = "ko-KR";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        recognition.continuous = false;

        // 음성인식 시작 전에 모달 표시
        showModal(speechModal);

        recognition.onstart = function () {
            // 음성인식이 시작될 때 모달을 확실히 표시
            showModal(speechModal);
        };

        recognition.onresult = async function (event) {
            const transcript = event.results[0][0].transcript;

            if (useAI) {
                hideModal(speechModal);
                setTimeout(() => {
                    showModal(aiProcessingModal);
                }, 300);

                try {
                    const response = await fetch("/app/ai/gpt4o/", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/x-www-form-urlencoded",
                            "X-CSRFToken": document.querySelector('[name="csrfmiddlewaretoken"]').value,
                        },
                        body: `text=${encodeURIComponent(transcript)}&style=${encodeURIComponent(user_style)}`,
                    });

                    if (!response.ok) throw new Error("AI 처리 실패");
                    const data = await response.json();
                    // 기존 텍스트에 새로운 텍스트 추가 (공백으로 연결)
                    const newText = data.result || transcript;
                    targetInput.value = targetInput.value
                        ? `${targetInput.value} ${newText}`
                        : newText;
                } catch (error) {
                    console.error("AI 처리 오류:", error);
                    // 에러 시에도 기존 텍스트 보존 (공백으로 연결)
                    targetInput.value = targetInput.value
                        ? `${targetInput.value} ${transcript}`
                        : transcript;
                } finally {
                    setTimeout(() => {
                        hideModal(aiProcessingModal);
                    }, 500);
                }
            } else {
                // 일반 음성인식에서도 기존 텍스트 보존 (공백으로 연결)
                targetInput.value = targetInput.value
                    ? `${targetInput.value} ${transcript}`
                    : transcript;
                setTimeout(() => {
                    hideModal(speechModal);
                }, 500);
            }
        };

        recognition.onerror = function (event) {
            console.error("음성 인식 오류:", event.error);
            setTimeout(() => {
                hideModal(speechModal);
            }, 300);
            alert("음성 인식 중 오류가 발생했습니다.");
        };

        recognition.onend = function () {
            // 음성인식 종료 시 자동으로 모달을 닫지 않음
            // 결과 처리 후 각각의 상황에서 모달을 닫도록 함
        };

        // 음성인식 시작
        setTimeout(() => {
            try {
                recognition.start();
            } catch (error) {
                console.error("음성 인식 시작 오류:", error);
                hideModal(speechModal);
            }
        }, 100);
    }

    if (generateBtn) {
        generateBtn.addEventListener("click", generateImage);
    }
    if (voiceInputBtn) {
        voiceInputBtn.addEventListener("click", () => handleVoiceInput(false));
    }
    if (aiVoiceInputBtn) {
        aiVoiceInputBtn.addEventListener("click", () => {
            const user_style = aiVoiceInputBtn.getAttribute("data-user-style");
            handleVoiceInput(true, user_style);
        });
    }

    if (searchInput) {
        searchInput.addEventListener("keypress", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                generateImage();
            }
        });
    }

    // Add form submit handler
    const postForm = document.getElementById("postForm");
    if (postForm) {
        postForm.addEventListener("submit", function (e) {
            e.preventDefault();
            if (!validateForm()) {
                return;
            }
            document.querySelector("#loadingModal div").innerText = "저장중...";
            showLoadingModal();
            this.submit();
        });
    }
});
