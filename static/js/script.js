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

    // 전역 변수로 recognition 객체와 상태 관리
    let recognition = null;
    let isRecognitionActive = false;

    function handleVoiceInput(useAI = false, user_style) {
        // 이미 음성 인식이 실행 중이면 중단
        if (isRecognitionActive) {
            console.log("음성 인식이 이미 실행 중입니다.");
            return;
        }

        if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
            alert("이 브라우저는 음성 인식을 지원하지 않습니다.");
            return;
        }

        // 이전 recognition 객체가 있다면 정리
        if (recognition) {
            try {
                recognition.abort();
                recognition.stop();
            } catch (e) {
                console.log("이전 음성 인식 세션 정리:", e);
            }
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = "ko-KR";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        recognition.continuous = false;

        // 입력 가능한 모든 필드 조회
        const inputFields = Array.from(document.querySelectorAll('input[type="text"], textarea')).filter((input) => !input.readOnly && !input.disabled && input.style.display !== "none");

        // 타겟 입력 필드 선택 (마지막 포커스 필드 또는 첫 번째 편집 가능한 필드)
        const targetInput = lastFocusedInput && !lastFocusedInput.readOnly && !lastFocusedInput.disabled ? lastFocusedInput : inputFields[0];

        if (!targetInput) {
            console.error("음성 입력을 처리할 수 있는 입력 필드를 찾을 수 없습니다.");
            alert("음성 입력을 처리할 수 있는 입력 필드를 찾을 수 없습니다.");
            return;
        }

        showModal(speechModal);
        isRecognitionActive = true;

        recognition.onstart = function () {
            isRecognitionActive = true;
            showModal(speechModal);
        };

        recognition.onend = function () {
            isRecognitionActive = false;
            // 모달은 결과 처리 후에 닫도록 유지
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
                    targetInput.value = targetInput.value ? `${targetInput.value} ${newText}` : newText;
                } catch (error) {
                    console.error("AI 처리 오류:", error);
                    // 에러 시에도 기존 텍스트 보존 (공백으로 연결)
                    targetInput.value = targetInput.value ? `${targetInput.value} ${transcript}` : transcript;
                } finally {
                    setTimeout(() => {
                        hideModal(aiProcessingModal);
                    }, 500);
                }
            } else {
                // 일반 음성인식에서도 기존 텍스트 보존 (공백으로 연결)
                targetInput.value = targetInput.value ? `${targetInput.value} ${transcript}` : transcript;
                setTimeout(() => {
                    hideModal(speechModal);
                }, 500);
            }
        };

        recognition.onerror = function (event) {
            console.error("음성 인식 오류:", event.error);
            isRecognitionActive = false;
            setTimeout(() => {
                hideModal(speechModal);
            }, 300);
            alert("음성 인식 중 오류가 발생했습니다.");
        };

        // 음성인식 시작 시 에러 처리 개선
        setTimeout(() => {
            try {
                recognition.start();
            } catch (error) {
                console.error("음성 인식 시작 오류:", error);
                isRecognitionActive = false;
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

    // if (searchInput) {
    //     searchInput.addEventListener("keypress", function (e) {
    //         if (e.key === "Enter") {
    //             e.preventDefault();
    //             generateImage();
    //         }
    //     });
    // }

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

    async function generateImage() {
        const prompt = searchInput.value.trim();

        if (!prompt) {
            alert("프롬프트를 입력해주세요.");
            return;
        }

        generateBtn.disabled = true;
        const originalText = generateBtn.innerHTML;
        generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 생성중...';

        try {
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
            const response = await fetch("/app/ai/generate/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": csrfToken,
                },
                body: `prompt=${encodeURIComponent(prompt)}`,
            });

            if (!response.ok) {
                throw new Error("이미지 생성에 실패했습니다.");
            }

            const data = await response.json();

            window.location.href = `/app/create/?${new URLSearchParams({
                image_url: data.image_url,
                generated_prompt: data.generated_prompt,
                original_prompt: prompt,
            }).toString()}`;
        } catch (error) {
            alert(error.message);
            console.error("Error:", error);
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerHTML = originalText;
        }
    }

    // generateBtn.addEventListener("click", generateImage);
    voiceInputBtn.addEventListener("click", () => handleVoiceInput(false)); // 기존 이벤트 핸들러
    // 변경: data attribute를 사용하여 HTML에서 user_style 값을 읽어 전달
    aiVoiceInputBtn.addEventListener("click", () => {
        const user_style = aiVoiceInputBtn.getAttribute("data-user-style");
        handleVoiceInput(true, user_style);
    });

    // searchInput.addEventListener("keypress", function (e) {
    //     if (e.key === "Enter") {
    //         e.preventDefault();
    //         generateImage();
    //     }
    // });
});
