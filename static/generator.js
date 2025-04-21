document.addEventListener('DOMContentLoaded', function () {
    console.log("문제 생성 페이지 로드됨");

    // 탭 기능
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function () {
            // 탭 활성화 상태 변경
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            // 콘텐츠 표시 전환
            const tabId = this.getAttribute('data-tab');
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
            });
            document.getElementById(tabId + '-tab').classList.remove('hidden');
        });
    });

    // 비교 탭 기능
    const comparisonTabs = document.querySelectorAll('[data-compare-tab]');
    if (comparisonTabs) {
        comparisonTabs.forEach(tab => {
            tab.addEventListener('click', function () {
                // 탭 활성화 상태 변경
                comparisonTabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                // 콘텐츠 표시 전환
                const tabId = this.getAttribute('data-compare-tab');
                document.querySelectorAll('.compare-tab-content').forEach(content => {
                    content.classList.add('hidden');
                });
                document.getElementById(tabId + '-tab').classList.remove('hidden');
            });
        });
    }

    // 인라인 편집 기능 구현
    const editableFields = document.querySelectorAll('.editable-script, .editable-msg');
    const jsonEditor = document.getElementById('json-editor');
    const contentField = document.getElementById('content-field');
    const regenerateContentField = document.getElementById('regenerate-content-field');
    let parsedContent = null;

    try {
        if (jsonEditor && jsonEditor.value && jsonEditor.value.trim()) {
            parsedContent = JSON.parse(jsonEditor.value);
            console.log("JSON 초기 파싱 성공:", typeof parsedContent);
        } else {
            console.log("JSON 에디터가 비어있거나 존재하지 않음");
        }
    } catch (e) {
        console.error('JSON 파싱 오류(초기화):', e);
        // 초기 파싱 실패 시에도 UI는 정상적으로 보여줘야 함
    }

    // 인라인 필드 변경 시 JSON 업데이트
    if (editableFields) {
        editableFields.forEach(field => {
            field.addEventListener('input', updateJsonFromFields);
        });
    }

    // 라디오 버튼 변경 시 정답 인덱스 업데이트
    const answerRadios = document.querySelectorAll('input[name="answer_index"]');
    if (answerRadios) {
        answerRadios.forEach(radio => {
            radio.addEventListener('change', function () {
                if (parsedContent) {
                    parsedContent.answer_index = parseInt(this.value);
                    updateJsonEditor();
                }
            });
        });
    }

    // 대화 라인 추가 버튼
    const addALineBtn = document.getElementById('add-a-line');
    const addBLineBtn = document.getElementById('add-b-line');

    if (addALineBtn) {
        addALineBtn.addEventListener('click', function () {
            addDialogueLine('A');
        });
    }

    if (addBLineBtn) {
        addBLineBtn.addEventListener('click', function () {
            addDialogueLine('B');
        });
    }

    // 선택지 추가 버튼
    const addChoiceBtn = document.getElementById('add-choice');
    if (addChoiceBtn) {
        addChoiceBtn.addEventListener('click', function () {
            addChoice();
        });
    }

    // JSON 편집기 이벤트
    const validateJsonBtn = document.getElementById('validate-json');
    const formatJsonBtn = document.getElementById('format-json');
    const jsonValidationMsg = document.getElementById('json-validation-message');

    if (validateJsonBtn) {
        validateJsonBtn.addEventListener('click', function () {
            validateJson();
        });
    }

    if (formatJsonBtn) {
        formatJsonBtn.addEventListener('click', function () {
            formatJson();
        });
    }

    // 폼 제출 전 JSON 유효성 검사 및 필드 업데이트
    const confirmForm = document.getElementById('confirm-form');
    if (confirmForm) {
        confirmForm.addEventListener('submit', function (e) {
            e.preventDefault(); // 일단 기본 제출 동작 방지

            try {
                // 콘텐츠 필드 확인
                const contentField = document.getElementById('content-field');
                if (!contentField) {
                    alert('콘텐츠 필드를 찾을 수 없습니다.');
                    return;
                }

                // 현재 활성화된 탭 확인
                const activeTab = document.querySelector('.tab.active').getAttribute('data-tab');

                // JSON 데이터 준비
                let jsonData = {};

                if (activeTab === 'json') {
                    // JSON 탭에서 제출 시 JSON 유효성 검사
                    if (!jsonEditor) {
                        alert('JSON 에디터를 찾을 수 없습니다.');
                        return;
                    }

                    const jsonText = jsonEditor.value.trim();
                    if (!jsonText) {
                        alert("JSON 데이터가 비어 있습니다.");
                        return;
                    }

                    try {
                        jsonData = JSON.parse(jsonText);
                        console.log("JSON 파싱 성공:", typeof jsonData);
                    } catch (error) {
                        alert('유효하지 않은 JSON 형식입니다: ' + error.message);
                        return;
                    }
                }
                else if (activeTab === 'edit') {
                    // 인라인 편집 탭에서 제출 시 필드에서 JSON 업데이트
                    updateJsonFromFields();

                    if (!parsedContent) {
                        alert('인라인 편집 내용을 JSON으로 변환할 수 없습니다.');
                        return;
                    }
                    jsonData = parsedContent;
                }
                else {
                    // 미리보기 탭에서는 현재 hidden 필드 값 사용
                    try {
                        if (!contentField.value || contentField.value.trim() === '') {
                            alert('콘텐츠 데이터가 비어 있습니다.');
                            return;
                        }
                        jsonData = JSON.parse(contentField.value);
                    } catch (error) {
                        alert('콘텐츠 필드에 유효하지 않은 JSON이 있습니다: ' + error.message);
                        return;
                    }
                }

                // 유효성 검사 성공 - 콘텐츠 필드에 JSON 설정
                contentField.value = JSON.stringify(jsonData);
                console.log("저장할 JSON:", typeof jsonData);

                // 정상 제출
                confirmForm.submit();
            } catch (error) {
                console.error("폼 제출 처리 중 오류:", error);
                alert('폼 제출 처리 중 오류가 발생했습니다: ' + error.message);
            }
        });
    }

    // 재생성 폼 처리
    const regenerateForm = document.getElementById('regenerate-form');
    if (regenerateForm) {
        regenerateForm.addEventListener('submit', function (e) {
            e.preventDefault(); // 기본 제출 동작 방지

            try {
                // 사용자 코멘트 필드 검증
                const userComment = document.getElementById('user_comment');
                if (!userComment || !userComment.value || userComment.value.trim() === '') {
                    alert('추가 요구사항을 입력해주세요.');
                    return;
                }

                // 재생성 필드
                const regenerateContentField = document.getElementById('regenerate-content-field');
                if (!regenerateContentField) {
                    alert('콘텐츠 필드를 찾을 수 없습니다.');
                    return;
                }

                // 현재 활성 탭 확인
                const activeTab = document.querySelector('.tab.active').getAttribute('data-tab');

                // JSON 데이터 준비
                let jsonData = {};

                if (activeTab === 'json' && jsonEditor) {
                    // JSON 에디터에서 직접 값을 가져옴
                    const jsonText = jsonEditor.value.trim();
                    if (!jsonText) {
                        alert('JSON 데이터가 비어 있습니다.');
                        return;
                    }

                    // JSON 파싱 시도
                    try {
                        jsonData = JSON.parse(jsonText);
                    } catch (error) {
                        alert('유효하지 않은 JSON 형식입니다: ' + error.message);
                        return;
                    }
                }
                else if (activeTab === 'edit' && parsedContent) {
                    // 편집 필드에서 JSON 업데이트
                    updateJsonFromFields();
                    jsonData = parsedContent;
                }
                else {
                    // 미리보기 탭 - hidden 필드에서 JSON 가져오기
                    const contentField = document.getElementById('content-field');
                    if (!contentField || !contentField.value.trim()) {
                        alert('유효한 콘텐츠 데이터가 없습니다.');
                        return;
                    }

                    try {
                        jsonData = JSON.parse(contentField.value);
                    } catch (error) {
                        alert('콘텐츠 필드에 유효하지 않은 JSON이 있습니다: ' + error.message);
                        return;
                    }
                }

                // 재생성 필드에 JSON 데이터 설정 (문자열화)
                regenerateContentField.value = JSON.stringify(jsonData);

                // 로그 기록
                console.log('재생성 요청 데이터:', jsonData);

                // 폼 제출
                regenerateForm.submit();

            } catch (error) {
                console.error('재생성 폼 처리 중 오류:', error);
                alert('재생성 요청 처리 중 오류가 발생했습니다: ' + error.message);
            }
        });
    }

    // 인라인 필드에서 JSON 업데이트 함수
    function updateJsonFromFields() {
        if (!parsedContent) {
            try {
                if (jsonEditor && jsonEditor.value) {
                    parsedContent = JSON.parse(jsonEditor.value);
                } else {
                    console.error("JSON 에디터가 없거나 비어 있음");
                    return;
                }
            } catch (e) {
                console.error("updateJsonFromFields - JSON 파싱 실패:", e);
                return;
            }
        }

        try {
            // 각 편집 가능한 필드 처리
            editableFields.forEach(field => {
                const fieldName = field.getAttribute('data-field');
                const fieldIndex = field.hasAttribute('data-index') ? parseInt(field.getAttribute('data-index')) : null;

                if (fieldName === 'keywords') {
                    // 키워드 필드 특별 처리 - 쉼표로 구분된 문자열을 배열로 변환
                    const keywordsStr = field.value.trim();
                    const keywordsArray = keywordsStr ? keywordsStr.split(',').map(k => k.trim()) : [];
                    parsedContent[fieldName] = keywordsArray;
                }
                else if (fieldIndex !== null && Array.isArray(parsedContent[fieldName])) {
                    // 배열 필드 (대화, 선택지 등)
                    if (fieldName === 'dialogue') {
                        const isA = field.closest('.msg').classList.contains('a');
                        parsedContent[fieldName][fieldIndex] = (isA ? 'A: ' : 'B: ') + field.value;
                    } else {
                        parsedContent[fieldName][fieldIndex] = field.value;
                    }
                } else {
                    // 일반 텍스트 필드 (상황, 제목, 내용 등)
                    parsedContent[fieldName] = field.value;
                }
            });

            // JSON 편집기 업데이트
            updateJsonEditor();
        } catch (e) {
            console.error("필드 업데이트 중 오류:", e);
        }
    }

    // JSON 편집기 업데이트 함수
    function updateJsonEditor() {
        if (parsedContent && jsonEditor) {
            try {
                jsonEditor.value = JSON.stringify(parsedContent, null, 2);
                if (contentField) {
                    contentField.value = JSON.stringify(parsedContent);
                }
                if (regenerateContentField) {
                    regenerateContentField.value = JSON.stringify(parsedContent);
                }
            } catch (e) {
                console.error("JSON 편집기 업데이트 중 오류:", e);
            }
        }
    }

    // JSON 유효성 검사 함수
    function validateJson() {
        if (!jsonEditor || !jsonValidationMsg) return;

        try {
            const jsonText = jsonEditor.value.trim();
            if (!jsonText) {
                showValidationError("JSON 데이터가 비어 있습니다.");
                return;
            }

            const json = JSON.parse(jsonText);
            showValidationSuccess('유효한 JSON 형식입니다.');
            parsedContent = json;
            if (contentField) {
                contentField.value = jsonEditor.value;
            }
            if (regenerateContentField) {
                regenerateContentField.value = jsonEditor.value;
            }
        } catch (e) {
            showValidationError('유효하지 않은 JSON 형식입니다: ' + e.message);
        }
    }

    // JSON 포맷팅 함수
    function formatJson() {
        if (!jsonEditor || !jsonValidationMsg) return;

        try {
            const jsonText = jsonEditor.value.trim();
            if (!jsonText) {
                showValidationError("JSON 데이터가 비어 있습니다.");
                return;
            }

            const json = JSON.parse(jsonText);
            jsonEditor.value = JSON.stringify(json, null, 2);
            showValidationSuccess('JSON 포맷팅 완료');
        } catch (e) {
            showValidationError('포맷팅 실패: 유효하지 않은 JSON 형식입니다.');
        }
    }

    // 유효성 검사 성공 메시지 표시
    function showValidationSuccess(message) {
        if (!jsonValidationMsg) return;
        jsonValidationMsg.textContent = message;
        jsonValidationMsg.className = 'alert alert-success mt-2';
        jsonValidationMsg.classList.remove('hidden');
    }

    // 유효성 검사 오류 메시지 표시
    function showValidationError(message) {
        if (!jsonValidationMsg) return;
        jsonValidationMsg.textContent = message;
        jsonValidationMsg.className = 'alert alert-danger mt-2';
        jsonValidationMsg.classList.remove('hidden');
    }

    // 대화 라인 추가 함수
    function addDialogueLine(speaker) {
        if (!parsedContent || !parsedContent.dialogue) {
            console.error("대화 라인 추가 실패: parsedContent 또는 dialogue 배열이 없습니다.");
            return;
        }

        const dialogueBox = document.querySelector('.dialogue-box');
        if (!dialogueBox) {
            console.error("대화 라인 추가 실패: .dialogue-box 요소를 찾을 수 없습니다.");
            return;
        }

        const newIndex = parsedContent.dialogue.length;
        const newText = speaker + ': ';

        // JSON 업데이트
        parsedContent.dialogue.push(newText);

        // UI 업데이트
        const newLine = document.createElement('div');
        newLine.className = `msg ${speaker.toLowerCase()}`;

        const newTextarea = document.createElement('textarea');
        newTextarea.className = 'editable-msg';
        newTextarea.setAttribute('data-field', 'dialogue');
        newTextarea.setAttribute('data-index', newIndex);
        newTextarea.addEventListener('input', updateJsonFromFields);

        newLine.appendChild(newTextarea);
        dialogueBox.appendChild(newLine);

        // JSON 편집기 업데이트
        updateJsonEditor();
    }

    // 선택지 추가 함수
    function addChoice() {
        if (!parsedContent || !parsedContent.choices) {
            console.error("선택지 추가 실패: parsedContent 또는 choices 배열이 없습니다.");
            return;
        }

        const choicesContainer = document.querySelector('.script-container');
        if (!choicesContainer) {
            console.error("선택지 추가 실패: .script-container 요소를 찾을 수 없습니다.");
            return;
        }

        const newIndex = parsedContent.choices.length;

        // JSON 업데이트
        parsedContent.choices.push('새 선택지');

        // UI 업데이트
        const newChoiceGroup = document.createElement('div');
        newChoiceGroup.className = 'form-group';

        const newChoiceFlex = document.createElement('div');
        newChoiceFlex.className = 'd-flex gap-2 items-center';

        const numberSpan = document.createElement('span');
        numberSpan.textContent = (newIndex + 1) + '.';

        const newTextarea = document.createElement('textarea');
        newTextarea.className = 'editable-script';
        newTextarea.setAttribute('data-field', 'choices');
        newTextarea.setAttribute('data-index', newIndex);
        newTextarea.textContent = '새 선택지';
        newTextarea.addEventListener('input', updateJsonFromFields);

        const radioLabel = document.createElement('label');
        radioLabel.className = 'd-flex items-center gap-2';

        const radioInput = document.createElement('input');
        radioInput.type = 'radio';
        radioInput.name = 'answer_index';
        radioInput.value = newIndex;
        radioInput.addEventListener('change', function () {
            parsedContent.answer_index = parseInt(this.value);
            updateJsonEditor();
        });

        const radioSpan = document.createElement('span');
        radioSpan.textContent = '정답';

        radioLabel.appendChild(radioInput);
        radioLabel.appendChild(radioSpan);

        newChoiceFlex.appendChild(numberSpan);
        newChoiceFlex.appendChild(newTextarea);
        newChoiceFlex.appendChild(radioLabel);

        newChoiceGroup.appendChild(newChoiceFlex);

        // 버튼 앞에 새 선택지 추가
        const addButton = document.getElementById('add-choice');
        if (addButton) {
            choicesContainer.insertBefore(newChoiceGroup, addButton);
        } else {
            choicesContainer.appendChild(newChoiceGroup);
        }

        // JSON 편집기 업데이트
        updateJsonEditor();
    }
});