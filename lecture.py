import streamlit as st
import PyPDF2
import os
import json
import re
import time
from dotenv import load_dotenv
import google.generativeai as genai


import google.generativeai as genai

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key = st.sidebar.text_input("Nhập Google API Key", type="password", value=st.session_state.api_key)

if api_key and api_key != st.session_state.api_key:
    st.session_state.api_key = api_key
    genai.configure(api_key=api_key)
    st.sidebar.success("API Key đã được cấu hình!")

if not api_key:
    st.sidebar.warning("Vui lòng nhập API Key để sử dụng app.")
    st.stop()

# === Load API Key ===
# load_dotenv()
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# genai.configure(api_key=GOOGLE_API_KEY)

# === Trích xuất văn bản từ PDF ===
def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# === Làm sạch JSON trả về từ Gemini ===
def extract_json_from_response(text):
    cleaned = re.sub(r"```(?:json)?|```", "", text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None

# === Chuẩn hóa lại format câu hỏi/trả lời về dạng dict options ===
def normalize_questions(questions):
    for q in questions:
        opts = q.get("options", [])
        if isinstance(opts, list) and len(opts) == 4:
            labeled_options = ['A', 'B', 'C', 'D']
            options_dict = dict(zip(labeled_options, opts))
            q["options"] = options_dict

            ans_text = q.get("answer", "").strip()
            matched_label = None
            for label, text in options_dict.items():
                if ans_text == text:
                    matched_label = label
                    break
            if matched_label:
                q["answer"] = matched_label
            else:
                q["answer"] = q["answer"].strip().upper()
    return questions

# === Gọi Gemini để tạo câu hỏi ===
def generate_questions_with_gemini(text, num_questions=3):
    prompt = f"""
    Từ đoạn văn sau, hãy tạo {num_questions} câu hỏi trắc nghiệm cùng với 4 lựa chọn và đáp án đúng.

    Trả về đúng định dạng JSON, không thêm mô tả, không markdown, không ```json.

    Văn bản:
    \"\"\"{text}\"\"\"

    Định dạng:
    [
        {{
            "question": "Câu hỏi?",
            "options": ["Nội dung đáp án A", "Nội dung đáp án B", "Nội dung đáp án C", "Nội dung đáp án D"],
            "answer": "Nội dung đáp án đúng"
        }},
        ...
    ]
    """
    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
    response = model.generate_content(prompt)

    try:
        raw_text = response.parts[0].text
        questions = extract_json_from_response(raw_text)
        if not questions:
            st.error("❌ Không thể phân tích JSON từ Gemini. Vui lòng thử lại.")
            return []
        return normalize_questions(questions)
    except Exception as e:
        st.error(f"❌ Lỗi khi xử lý phản hồi từ Gemini: {e}")
        return []

# === Giao diện chính ===
st.set_page_config(page_title="Tạo Câu Hỏi Trắc Nghiệm", layout="centered")
st.title("📄🧠 Tạo Câu Hỏi Trắc Nghiệm từ PDF với Gemini")



uploaded_file = st.file_uploader("📤 Tải lên file PDF", type="pdf")

if uploaded_file:
    # Khi nhấn "Tạo bộ câu hỏi mới", xóa toàn bộ state liên quan để tạo mới
    if st.button("♻️ Tạo bộ câu hỏi mới") or "questions" not in st.session_state:
        for key in ["questions", "user_answers", "submitted", "start_time", "end_time", "result_log"]:
            if key in st.session_state:
                del st.session_state[key]

        text = extract_text_from_pdf(uploaded_file)
        st.success("✅ Đã trích xuất nội dung từ PDF!")

        num_questions = st.slider("📌 Chọn số lượng câu hỏi muốn tạo:", 1, 10, 3)

        if st.button("🚀 Tạo câu hỏi với Gemini"):
            st.session_state.questions = generate_questions_with_gemini(text, num_questions)
            st.session_state.start_time = time.time()
            st.session_state.submitted = False
            st.rerun()

    elif "questions" in st.session_state:
        questions = st.session_state.questions
        st.write("## 📚 Câu hỏi trắc nghiệm")
        user_answers = []

        for idx, q in enumerate(questions):
            st.markdown(f"**Câu {idx + 1}:** {q['question']}")
            options_display = [f"{key}. {val}" for key, val in q["options"].items()]
            # Nếu đã có câu trả lời trước đó thì dùng làm mặc định
            default_option = None
            if "user_answers" in st.session_state and len(st.session_state.user_answers) > idx:
                selected_label = st.session_state.user_answers[idx]
                # Tìm nội dung option tương ứng
                for opt in options_display:
                    if opt.startswith(selected_label):
                        default_option = opt
                        break
            selected = st.radio("Chọn đáp án:", options_display, key=f"q_{idx}", index=options_display.index(default_option) if default_option else 0)
            user_choice = selected[0]
            user_answers.append(user_choice)

        if st.button("📊 Nộp bài và xem kết quả"):
            st.session_state.user_answers = user_answers
            st.session_state.submitted = True
            st.session_state.end_time = time.time()

        if st.session_state.get("submitted"):
            score = 0
            total = len(questions)

            for idx, q in enumerate(questions):
                correct = q["answer"].strip().upper()
                user_ans = st.session_state.user_answers[idx].strip().upper()
                if user_ans == correct:
                    st.success(f"Câu {idx + 1}: ✅ Đúng")
                    score += 1
                else:
                    st.error(f"Câu {idx + 1}: ❌ Sai — Đáp án đúng: {correct}")

            elapsed_time = round(st.session_state.end_time - st.session_state.start_time, 2)
            st.info(f"🎯 Kết quả: {score}/{total} đúng")
            st.info(f"⏱️ Thời gian làm bài: {elapsed_time} giây")

            # Lưu log mỗi lần làm bài
            if "logs" not in st.session_state:
                st.session_state.logs = []
            # Lưu log chỉ khi mới submit, tránh lưu nhiều lần khi rerun
            if "last_submit_time" not in st.session_state or st.session_state.last_submit_time != st.session_state.end_time:
                st.session_state.logs.append({
                    "score": score,
                    "total": total,
                    "time": elapsed_time,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                })
                st.session_state.last_submit_time = st.session_state.end_time

            # Lưu kết quả vào session để giữ trạng thái
            st.session_state.result_log = {
                "score": score,
                "total": total,
                "time": elapsed_time,
            }

        # Nút làm lại bộ hiện tại, chỉ reset câu trả lời, không mất điểm và thời gian
        if st.button("🔁 Làm lại bộ hiện tại"):
            if "user_answers" in st.session_state:
                del st.session_state["user_answers"]
            if "submitted" in st.session_state:
                del st.session_state["submitted"]
            if "end_time" in st.session_state:
                del st.session_state["end_time"]
            # Giữ nguyên start_time và questions
            st.rerun()


else:
    st.info("Vui lòng tải lên file PDF để bắt đầu.")
