import streamlit as st
import pandas as pd


# 1. 读取 Excel 题目（仅适配你的格式：题型、题目、选项、正确答案）
@st.cache_data
def load_questions(file_path):
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        # 强制指定列名（确保和你的 Excel 一致）
        df.columns = ["题型", "题目", "选项", "正确答案", "备注"]  # 最后一列是备注，忽略即可
        # 校验核心列
        required_cols = ["题型", "题目", "选项", "正确答案"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Excel 缺少必要列：{', '.join(missing_cols)}")
            st.stop()
        return df
    except Exception as e:
        st.error(f"读取 Excel 失败：{str(e)}")
        st.error("请确认：1. 文件是 .xlsx 格式 2. 列名包含「题型、题目、选项、正确答案」")
        st.stop()


# 2. 初始化应用状态（新增：记录当前题的正确答案显示状态）
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0  # 当前题目索引
    st.session_state.score = 0  # 得分
    st.session_state.quiz_finished = False  # 答题是否结束
    st.session_state.show_answer = False  # 是否显示当前题的正确答案

# 3. 页面配置
st.set_page_config(page_title="网约车答题应用", page_icon="🚗")
st.title("🚗 网约车答题应用")

# 4. 上传 Excel 文件
uploaded_file = st.file_uploader("请上传网约车题目 Excel（.xlsx 格式）", type="xlsx")
if uploaded_file is not None:
    df = load_questions(uploaded_file)
    total_questions = len(df)

    # 校验题目数量
    if total_questions == 0:
        st.error("Excel 中未检测到题目数据！")
        st.stop()

    remaining_questions = total_questions - st.session_state.current_question - 1

    # 侧边栏：进度和得分
    st.sidebar.header("答题进度")
    st.sidebar.metric("剩余题目", remaining_questions)
    st.sidebar.metric("当前得分", st.session_state.score)
    st.sidebar.progress((st.session_state.current_question + 1) / total_questions)

    # 5. 答题界面
    if not st.session_state.quiz_finished:
        row = df.iloc[st.session_state.current_question]
        question_type = row["题型"]
        question = row["题目"]
        options_text = row["选项"]
        correct_answer = row["正确答案"]

        # 显示题目信息
        st.subheader(f"第 {st.session_state.current_question + 1} 题 / 共 {total_questions} 题")
        st.write(f"**题型：** {question_type}")
        st.write(f"**题目：** {question}")

        # ========== 仅适配你的题型逻辑 ==========
        user_answer = None
        # 👉 判断题
        if question_type == "判断题":
            user_answer = st.radio("请选择答案：", ("对", "错"), key=f"q_{st.session_state.current_question}")

        # 👉 单选题（你的格式：选项在一列，换行分隔 A.xxx\nB.xxx）
        elif question_type == "单选题":
            # 解析「选项」列，过滤空行
            options = [opt.strip() for opt in str(options_text).splitlines() if opt.strip()]
            if not options:
                st.error("该单选题缺少选项！")
                st.stop()
            # 提取选项标签（A/B/C）和内容
            display_options = []
            for opt in options:
                if "." in opt:
                    display_options.append(opt)
                else:
                    # 兼容没有点的情况，比如 "A 3年"
                    display_options.append(f"{opt[0]}. {opt[1:].strip()}")

            # 显示单选按钮
            user_answer = st.radio("请选择答案：", display_options, key=f"q_{st.session_state.current_question}")
            user_answer = user_answer.split(".")[0]  # 提取 A/B/C

        # 👉 多选题（你的格式：选项在一列，换行分隔）
        elif question_type == "多选题":
            # 解析「选项」列
            options = [opt.strip() for opt in str(options_text).splitlines() if opt.strip()]
            if not options:
                st.error("该多选题缺少选项！")
                st.stop()
            display_options = []
            for opt in options:
                if "." in opt:
                    display_options.append(opt)
                else:
                    display_options.append(f"{opt[0]}. {opt[1:].strip()}")

            # 显示多选框
            selected_options = st.multiselect("请选择答案（可多选）：", display_options,
                                              key=f"q_{st.session_state.current_question}")
            # 拼接答案（排序后，如 AC/ABD）
            user_answer = "".join([opt.split(".")[0] for opt in sorted(selected_options)])

        else:
            st.error(f"不支持的题型：{question_type}，仅支持「判断题」「单选题」「多选题」")
            st.stop()

        # ========== 提交按钮逻辑（核心修改：提交后显示正确答案） ==========
        btn_text = "下一题" if st.session_state.current_question < total_questions - 1 else "完成答题"
        if st.button(btn_text, type="primary"):
            # 答案判断
            if user_answer == correct_answer:
                st.session_state.score += 1
                st.success("✅ 回答正确！")
            else:
                st.error(f"❌ 回答错误！")

            # 提交后显示正确答案
            st.session_state.show_answer = True

            # 延迟切换题目（让用户先看到正确答案），如果是最后一题则直接结束
            if st.session_state.current_question < total_questions - 1:
                # 这里不立即切换，而是等用户看完成绩后手动点下一题（新增按钮）
                pass
            else:
                st.session_state.quiz_finished = True
                st.rerun()

        # ========== 显示正确答案区域 ==========
        if st.session_state.show_answer:
            st.divider()  # 分割线
            st.info(f"📌 本题正确答案：**{correct_answer}**")

            # 如果是单选题/多选题，还显示正确答案对应的选项文本
            if question_type in ["单选题", "多选题"]:
                # 解析选项，找到正确答案对应的文本
                options = [opt.strip() for opt in str(options_text).splitlines() if opt.strip()]
                correct_option_text = ""
                for opt in options:
                    opt_label = opt.split(".")[0]
                    # 多选题兼容（如正确答案是AC，遍历每个字母）
                    if (question_type == "单选题" and opt_label == correct_answer) or \
                            (question_type == "多选题" and opt_label in correct_answer):
                        correct_option_text += f"{opt}\n"
                if correct_option_text:
                    st.write(f"✅ 正确选项：\n{correct_option_text}")

            # 新增「确认并进入下一题」按钮（只有非最后一题显示）
            if st.session_state.current_question < total_questions - 1:
                if st.button("确认并进入下一题", type="secondary"):
                    st.session_state.current_question += 1
                    st.session_state.show_answer = False  # 重置正确答案显示状态
                    st.rerun()

    # 6. 答题结束页面
    else:
        st.balloons()
        st.subheader("🏆 答题完成！")
        accuracy = (st.session_state.score / total_questions) * 100

        # 结果展示
        col1, col2, col3 = st.columns(3)
        col1.metric("总题数", total_questions)
        col2.metric("答对题数", st.session_state.score)
        col3.metric("正确率", f"{accuracy:.1f}%")

        # 重新答题按钮
        if st.button("🔄 重新答题", type="primary"):
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.quiz_finished = False
            st.session_state.show_answer = False  # 重置正确答案显示状态
            st.rerun()
