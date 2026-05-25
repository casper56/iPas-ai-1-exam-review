import os
import re
import json
import shutil

# ==========================================
# 1. 專案路徑與基本設定
# ==========================================
BACKUP_DIR = "./backups"
TXT_DIR = "./scratch/txt"
OUTPUT_HTML = "./index.html"
OUTPUT_JSON = "./scratch/parsed_questions.json"

print("==================================================")
print("   iPAS AI 應用規劃師 考古題複習系統一鍵生成工具 V2")
print("==================================================")

# ==========================================
# 2. 備份現有的 index.html 與 build_exam_system.py
# ==========================================
if os.path.exists(OUTPUT_HTML):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, "index.html.bak")
    shutil.copy2(OUTPUT_HTML, backup_path)
    print(f"[備份成功] 已將現有的 index.html 備份至: {backup_path}")

# ==========================================
# 3. 定義考題文字清洗與解析邏輯
# ==========================================
NOISE_PATTERNS = [
    r"^=== PAGE \d+ ===",
    r"^第 \d+ 頁，共 \d+ 頁",
    r"iPAS AI 應用規劃師",
    r"初級能力鑑定",
    r"考試樣題",
    r"公告試題",
    r"當次試題公告",
    r"考試日期：",
    r"試題公告日期：",
    r"^◆ 科目一：",
    r"^◆ 科目二：",
    r"^◆ 初級能力鑑定",
    r"^◆ 中級能力鑑定",
    r"^科目\s+題號\s+答案\s+題目",
    r"^題號\s+答案\s+題目",
    r"^答案\s+題目",
    r"^答案\s+題\s+目",
    r"^一、選擇題",
    r"^L11 人工智慧基礎",
    r"^概論",
    r"^L12 生成式 AI 應用",
    r"^與規劃",
    r"^L21 人工智慧技術",
    r"^應用與規劃",
    r"^L22 大數據處理分",
    r"^析與應用",
    r"^L23 機器學習技術",
    r"^與應用"
]

def clean_line(line):
    line = line.strip()
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, line):
            return ""
    return line

def parse_txt_file(file_path, file_type, default_year, default_subject):
    if not os.path.exists(file_path):
        print(f"[警告] 找不到檔案: {file_path}")
        return []

    print(f"[解析中] 正在讀取並解析: {os.path.basename(file_path)}...")
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned_lines = []
    for line in lines:
        cleaned = clean_line(line)
        if cleaned:
            cleaned_lines.append(cleaned)

    questions = []
    current_q = None
    
    formal_start_pattern = re.compile(r"^([A-DＡ-ＤＣｃ])\s*(\d+)\s*[\.．\s]\s*(.*)$")
    sample_start_pattern = re.compile(r"^(\d+)\s*[\.．]?\s*([A-DＡ-Ｄ])\s*(.*)$")

    for line in cleaned_lines:
        is_new = False
        ans, num, desc = "", 0, ""
        
        if file_type == 'formal':
            match = formal_start_pattern.match(line)
            if match:
                is_new = True
                ans = match.group(1).upper()
                if ans == 'Ｃ' or ans == 'ｃ': ans = 'C'
                ans = ans.replace('Ａ','A').replace('Ｂ','B').replace('Ｃ','C').replace('Ｄ','D')
                num = int(match.group(2))
                desc = match.group(3).strip()
        else:
            match = sample_start_pattern.match(line)
            if match:
                if not re.search(r"^\d+\s*[\.．]?\s*\(A\)", line):
                    is_new = True
                    num = int(match.group(1))
                    ans = match.group(2).upper()
                    ans = ans.replace('Ａ','A').replace('Ｂ','B').replace('Ｃ','C').replace('Ｄ','D')
                    desc = match.group(3).strip()
        
        if is_new:
            if current_q:
                questions.append(current_q)
            
            current_q = {
                "id": "",
                "num": num,
                "original_num": num,
                "year": default_year,
                "subject": default_subject,
                "desc": desc,
                "options": {"A": "", "B": "", "C": "", "D": ""},
                "answer": ans,
                "source": os.path.basename(file_path).replace(".txt", "")
            }
            continue

        if not current_q:
            continue

        opt_matches = list(re.finditer(r"\(([A-DＡ-Ｄ])\)", line))
        if opt_matches:
            for i, m in enumerate(opt_matches):
                opt_char = m.group(1).upper()
                opt_char = opt_char.replace('Ａ','A').replace('Ｂ','B').replace('Ｃ','C').replace('Ｄ','D')
                start_idx = m.end()
                end_idx = opt_matches[i+1].start() if i+1 < len(opt_matches) else len(line)
                opt_val = line[start_idx:end_idx].strip(" ；,，.．;:")
                current_q["options"][opt_char] = opt_val
        else:
            if not current_q["options"]["A"]:
                current_q["desc"] += "\n" + line
            else:
                for opt in ["D", "C", "B", "A"]:
                    if current_q["options"][opt]:
                        current_q["options"][opt] += "\n" + line
                        break

    if current_q:
        questions.append(current_q)

    for q in questions:
        q["desc"] = q["desc"].strip()
        for opt in ["A", "B", "C", "D"]:
            q["options"][opt] = q["options"][opt].strip()

    print(f"[解析成功] 自 {os.path.basename(file_path)} 成功解析出 {len(questions)} 題。")
    return questions

# ==========================================
# 4. 專家知識庫解析器 (Explanation Generator)
# ==========================================
def generate_explanation(q):
    desc = q["desc"].lower()
    opts = "".join([q["options"][k].lower() for k in ["A", "B", "C", "D"]])
    ans = q["answer"]
    
    # 基礎通用解析前綴
    prefix = f"💡 **【AI 智能學術解析】**\n本題正確答案為 **{ans}**。\n\n"
    
    # 進行考點關鍵字比對
    if "k-means" in desc or "k平均" in desc or "k-平均" in desc:
        return prefix + (
            "K-means (K-平均法) 是一種非監督式學習群集演算法，使用「距離度量（如歐氏距離）」來評估數據點相似度。\n"
            "- **核心限制**：由於計算距離需要連續的數值特徵，因此**無法直接處理類別型特徵 (Categorical Data)**。\n"
            "- **初始值敏感度**：不同的初始群集中心，常導致收斂至不同的局部最佳解。\n"
            "- **離群值敏感度**：因為中心點是取平均值，極易受到離群值 (Outliers) 與雜訊拉扯，破壞群集穩定性。"
        )
        
    if "過擬合" in desc or "overfitting" in desc or "欠擬合" in desc or "underfitting" in desc or "正則化" in desc or "regularization" in desc or "l1" in desc or "l2" in desc or "lasso" in desc:
        return prefix + (
            "過擬合 (Overfitting) 指模型在訓練集表現極佳，但在未知的測試集表現極差，即泛化能力差（高變異 High Variance）。\n"
            "- **L1 正則化 (Lasso)**：懲罰項為權重的絕對值之和。其核心特性是會使不重要特徵的權重精確收斂為 0，促使模型稀疏化，**非常適合用於特徵選擇**。\n"
            "- **L2 正則化 (Ridge)**：懲罰項為權重的平方和，使權重逼近於 0 但不為 0，能平滑權重、抑制過大權重，增加模型泛化效能。\n"
            "- **降低過擬合方法**：增加訓練資料量、降低模型複雜度、使用正則化或 Dropout 等。"
        )

    if "非監督" in desc or "unsupervised" in desc:
        return prefix + (
            "非監督式學習 (Unsupervised Learning) 處理**無標籤 (Labels)** 的數據集。\n"
            "- **核心特徵**：模型無需人手標註，純粹依據資料自身的空間特徵相似性（如距離）進行自動分群或探索隱含結構。\n"
            "- **典型代表**：K-means 群集分析、主成分分析 (PCA) 降維、關聯規則分析 (Apriori)。"
        )

    if "監督" in desc or "supervised" in desc:
        return prefix + (
            "監督式學習 (Supervised Learning) 指訓練資料包含明確的「輸入特徵」與「已知目標標籤 (Labels)」的機器學習方式。\n"
            "- **主要任務**：包含預測連續數值的「迴歸問題 (Regression)」與預測離散類別的「分類問題 (Classification)」。\n"
            "- **典型代表**：線性迴歸、決策樹、支援向量機 (SVM)、隨機森林。"
        )

    if "強化學習" in desc or "reinforcement" in desc:
        return prefix + (
            "強化學習 (Reinforcement Learning) 是讓智能體 (Agent) 在未知的環境中透過**試錯 (Trial-and-Error)** 進行學習的類型。\n"
            "- **核心機制**：智能體採取行動並獲得環境回饋的「獎勵 (Reward)」或「懲罰 (Penalty)」訊號，進而優化其長期的決策策略。\n"
            "- **適用場景**：適合解決下圍棋 (AlphaGo)、自動駕駛、機器人控制等需要連續與環境動態互動的問題。"
        )

    if "大數據" in desc or "big data" in desc or "特性" in desc and "資料" in desc:
        return prefix + (
            "大數據 (Big Data) 時代的資料具備著名的 4V 特性：\n"
            "1. **Volume (資料量極大)**：規模可達 TB 甚至 PB 級別。\n"
            "2. **Velocity (變動速度快)**：資料增長迅速，需要高時效的即時串流處理。\n"
            "3. **Variety (多樣性)**：包含結構化、半結構化（XML/JSON）及大量非結構化（圖像/影片）資料。\n"
            "4. **Veracity (真實性)**：資料可能包含大量雜訊，精準度與信賴度存在不確定性。\n"
            "- *注意*：「資料存儲位置固定」並非大數據特性，相反地，大數據通常採用高度分散式儲存。"
        )

    if "roc" in desc or "auc" in desc or "接受者操作特徵" in desc:
        return prefix + (
            "ROC 曲線 (Receiver Operating Characteristic Curve) 用於評估二元分類器的性能：\n"
            "- **X軸**：假陽性率 (FPR, False Positive Rate)，代表將正常樣本誤判為異常的機率。\n"
            "- **Y軸**：真陽性率 (TPR, True Positive Rate / 召回率)，代表成功偵測出異常樣本的機率。\n"
            "- **AUC (面積)**：ROC 曲線下的面積，數值在 0.5 (隨機猜測) 到 1.0 (完美分類) 之間。AUC 越接近 1，代表模型的整體分類效能越優異且穩定。"
        )

    if "smote" in desc or "不平衡" in desc or "imbalance" in desc:
        return prefix + (
            "在分類任務中，若某個類別的樣本數量遠少於其他類別（例如詐欺交易偵測、罕見疾病診斷），會導致「類別不平衡 (Class Imbalance)」問題。\n"
            "- **SMOTE (合成少數類別過採樣技術)**：不是簡單複製少數類別，而是依據少數類別樣本的特徵空間，尋找其最近鄰點，在兩點連線上隨機插值，**合成產生新的少數類別樣本**，能有效平滑分佈，避免模型過擬合多數類別。"
        )

    if "softmax" in desc:
        return prefix + (
            "Softmax 函數是深度學習中**多分類輸出層**最常用的激活函數。\n"
            "- **作用原理**：將輸出層各節點的原始分數 (Logits) 進行指數化與歸一化處理，將它們轉換成一組機率值（數值介於 0 到 1 之間，且**所有類別的機率總和精確為 1.0**）。\n"
            "- **應用**：串流平台影片推薦分類、圖像多分類預測等。"
        )

    if "sigmoid" in desc:
        return prefix + (
            "Sigmoid 函數常用於神經網路的**二分類輸出層**或傳統的邏輯迴歸中。\n"
            "- **作用原理**：公式為 $S(x) = 1 / (1 + e^{-x})$。它將任意實數輸入壓縮映射至 0 到 1 之間的數值，代表發生某事件（如退貨、流失）的機率機率分佈。"
        )

    if "gan" in desc or "生成對抗" in desc:
        return prefix + (
            "生成對抗網路 (GAN) 由生成器與鑑別器兩個核心神經網路組成，兩者在「極小化極大化 (Minimax Game)」的賽局對抗中共同成長：\n"
            "1. **生成器 (Generator)**：負責從隨機雜訊中，合成出高度逼真、能欺騙鑑別器的虛擬樣本數據。\n"
            "2. **鑑別器 (Discriminator)**：負責準確辨識輸入的數據是來自真實資料集，還是由生成器偽造的。\n"
            "- **特色**：GAN 的鑑別器旨在分類真假，它可用於評估生成器合成數據的品質，是典型的生成與評估對抗架構。"
        )

    if "no-code" in desc or "no code" in desc or "low code" in desc or "low-code" in desc or "低程式碼" in desc or "無程式碼" in desc:
        return prefix + (
            "No Code (無程式碼) / Low Code (低程式碼) 平台的核心目的在於降低技術複雜度與開發成本：\n"
            "- **Low Code**：更適合開發具有彈性且高擴充性的業務邏輯解決方案，因為它允許串接客製化程式碼以進行複雜整合。\n"
            "- **資安風險（影子 IT, Shadow IT）**：當非技術人員利用 Low-Code 平台迅速自行開發並發布應用程式時，若未經過企業內部 IT 部門的安全審核與中央管控，極易造成**敏感企業個資洩漏**或應用程式無序擴散的治理危機。"
        )

    if "etl" in desc or "extract" in desc:
        return prefix + (
            "ETL 是資料管道與資料倉儲的基石：\n"
            "1. **Extract (擷取)**：從多個異質來源系統中抽取原始數據。\n"
            "2. **Transform (轉換)**：對資料進行格式清理、品質校正、排序、去重或正規化（如統一金額單位）。\n"
            "3. **Load (載入)**：將清理妥當的資料寫入到目標儲存庫（如資料倉儲 Data Warehouse）中。"
        )

    if "貝氏" in desc or "bayes" in desc:
        return prefix + (
            "單純貝氏分類器 (Naive Bayes Classifier) 是一種基於**貝氏定理**的生成式模型 (Generative Model)。\n"
            "- **單純假設**：它作了「各項輸入特徵之間彼此條件獨立」的強烈假設，藉此建立聯合機率分佈，再依據條件機率進行推斷與預測。\n"
            "- **應用**：極度適合高維度的文字分類、垃圾郵件過濾。"
        )

    if "線性迴歸" in desc or "linear regression" in desc:
        return prefix + (
            "線性迴歸 (Linear Regression) 是經典的監督式機器學習模型，旨在找出特徵變數與連續型標籤變數之間的最佳線性擬合關係。\n"
            "- **適用場景**：專注於預測**連續數值**（例如：預測下一季的產品銷售數量、銷售額預測、房價預測）。"
        )

    if "資料整合" in desc or "data integration" in desc:
        return prefix + (
            "資料整合 (Data Integration) 的技術範疇著重於對齊多個異質來源的資料，整併其欄位，排除重複與格式差異，以確保分析時的一致性與完整性。\n"
            "- **注意**：依循資料保存政策延長資料的留存期限，是屬於**「資料治理 (Data Governance) / 法規合規」**的要求，而非資料整合的技術核心目的。"
        )

    if "one-hot" in desc or "獨熱" in desc:
        return prefix + (
            "One-hot 編碼 (獨熱編碼) 用於將無順序大小關係的**類別型特徵 (Categorical Features)** 轉換為機器學習模型可識別的稀疏數值向量。\n"
            "- **目的**：例如將「方案A, B, C」編碼為 `[1,0,0]`, `[0,1,0]`, `[0,0,1]`。這樣可以防止演算法誤將類別文字當作有大小順序的連續數值，避免模型誤判特徵重要性。"
        )

    if "寬深模型" in desc or "wide" in desc and "deep" in desc:
        return prefix + (
            "寬深模型 (Wide & Deep Model) 廣泛應用於廣告推薦與商品推薦系統中：\n"
            "- **Wide 組件**：負責「記憶 (Memorization)」，透過交叉積特徵變換，記住歷史中高頻出現、具體且強烈的特徵組合規律。\n"
            "- **Deep 組件**：負責「泛化 (Generalization)」，透過低維稀疏向量 (Embedding) 的深度神經網路，去預測與探索歷史未曾出現的新穎特徵組合。"
        )

    if "感知器" in desc or "傳感器" in desc or "sensor" in desc:
        return prefix + (
            "感知層或 **感知器感測網路 (Sensor Network)** 負責透過各種物理感測設備（如溫度計、PM2.5監測器），直接且持續地從現實物理世界收集動態的物理特徵數據與設備狀態，是物聯網與智慧調度系統（如智慧垃圾收集路線）的最底層數據來源。"
        )

    if "特徵交叉" in desc or "feature cross" in desc:
        return prefix + (
            "特徵交叉 (Feature Cross) 是一種強大的特徵工程技巧。\n"
            "- **作用原理**：透過將兩個或多個類別特徵進行乘積或組合（例如將「星期幾」和「24小時制時間」交叉結合成一個新特徵），可以使傳統的線性模型也能學習到非線性關係，從而大幅提升模型對通勤時間、轉換率等複雜複合場景的預測效能。"
        )

    if "自編碼器" in desc or "autoencoder" in desc:
        return prefix + (
            "自編碼器 (Autoencoder) 是一種基於非監督式學習的神經網路架構：\n"
            "- **重建誤差機制**：在訓練時僅使用正常樣本，模型會學會完美重建正常特徵。當異常樣本輸入時，重建誤差 (Reconstruction Error) 會顯著偏高，這使其**極佳地適用於異常偵測**。\n"
            "- **變分自編碼器 (VAE)**：進一步將隱變量建模為概率分佈，能依據隱空間生成風格一致且具有變化的全新樣本數據。"
        )

    if "cnn" in desc or "卷積" in desc:
        return prefix + (
            "卷積神經網路 (CNN) 具備「局部感受野 (Local Receptive Fields)」與「權重共享 (Weight Sharing)」的物理特性。\n"
            "- **核心優勢**：能高效擷取具空間相關性的局部特徵，因此最適合用於圖像識別、醫學影像分析、產品瑕疵檢測等視覺領域。"
        )

    if "lstm" in desc or "rnn" in desc or "遞迴" in desc or "時間序列" in desc:
        return prefix + (
            "遞迴神經網路 (RNN) 與長短期記憶網路 (LSTM) 內建內部狀態記憶機制。\n"
            "- **核心優勢**：最適合處理具備先後順序、前後文關聯、或時間相關步長的**序列型數據 (Sequence Data)**（如文字、語音、股市時間序列資料）。"
        )

    if "治理" in desc or "倫理" in desc or "規範" in desc or "法" in desc:
        return prefix + (
            "AI 治理 (AI Governance) 是國際推動安全 AI 的核心焦點：\n"
            "- **監管沙盒 (Regulatory Sandbox)**：指在受控的創新實驗環境中，暫時豁免部分法規，供創新技術試驗與風險評估。\n"
            "- **個資與隱私限制**：依個資法規定，若接收個資的國家個人資料保護法規尚未完善，中央目的事業主管機關有權限制該項國際傳輸，以保障當事人權益。"
        )

    if "人迴圈" in desc or "loop" in desc:
        return prefix + (
            "人在迴圈的決策監督機制通常分為以下幾種主要情境：\n"
            "1. **Human-in-the-loop (人在迴圈內)**：AI 僅提供建議，每一步決策在執行前，均必須經過人類的逐一審核與手動批准。\n"
            "2. **Human-over-the-loop (人在迴圈上)**：AI 可自主運行，但人類進行日常監督，必要時可立即介入修正、干預或中止其運行。\n"
            "3. **Human-out-of-the-loop (人在迴圈外)**：AI 具備完全自主決策與執行權，人類完全不參與日常運作的審核或控制。"
        )

    # 預設通用解析 (針對沒有特定考點的題目)
    if ans == "A":
        opt_analysis = "本題答案為 A。選項 A 所描述之核心定義與題幹背景最相符合。B, C, D 則存在概念混淆、或是偏離了該技術的適用邊界。"
    elif ans == "B":
        opt_analysis = "本題答案為 B。選項 B 準確表達了題幹核心問題的解決路徑。其餘選項在實務中皆存在邏輯缺陷，或是不符合最佳實踐規範。"
    elif ans == "C":
        opt_analysis = "本題答案為 C。選項 C 為正確解答。其他選項在學術定義上存在明顯偏差，或是不符合所討論技術的理論與物理基礎。"
    else:
        opt_analysis = "本題答案為 D。選項 D 與題目的學術邏輯和產業應用背景最為契合。選項 A, B, C 在定義上存在明顯錯誤或是邏輯倒置。"
        
    return prefix + opt_analysis + "\n\n💡 **【複習建議】**\n建議複習本題所涉及之 AI 基本概念與技術，重點在於區分選項中各核心專有名詞的學術適用邊界與限制。"

# ==========================================
# 5. 執行各個考卷的解析
# ==========================================
all_parsed_questions = []

all_parsed_questions.extend(parse_txt_file(
    os.path.join(TXT_DIR, "114年第四梯次初級AI應用規劃師第一科人工智慧基礎概論(當次試題公告114_20251226000442.txt"),
    file_type='formal',
    default_year="114年第四梯次",
    default_subject="人工智慧基礎概論"
))

all_parsed_questions.extend(parse_txt_file(
    os.path.join(TXT_DIR, "114年第四梯次初級AI應用規劃師第二科生成式AI應用與規劃(當次試題公告114_20251226000507.txt"),
    file_type='formal',
    default_year="114年第四梯次",
    default_subject="生成式AI應用與規劃"
))

all_parsed_questions.extend(parse_txt_file(
    os.path.join(TXT_DIR, "115年第一次初級AI應用規劃師_第一科_人工智慧基礎概論_公告試題_20260410164304.txt"),
    file_type='formal',
    default_year="115年第一次",
    default_subject="人工智慧基礎概論"
))

all_parsed_questions.extend(parse_txt_file(
    os.path.join(TXT_DIR, "115年第一次初級AI應用規劃師_第二科_生成式AI應用與規劃_公告試題_20260410164328.txt"),
    file_type='formal',
    default_year="115年第一次",
    default_subject="生成式AI應用與規劃"
))

raw_11409 = parse_txt_file(
    os.path.join(TXT_DIR, "iPAS+AI應用規劃師初級能力鑑定-考試樣題(114年9月版).txt"),
    file_type='sample',
    default_year="114年樣題(9月版)",
    default_subject="人工智慧基礎概論"
)
current_subject = "人工智慧基礎概論"
last_num = 0
for q in raw_11409:
    if q["num"] < last_num or (q["num"] == 1 and last_num > 20):
        current_subject = "生成式AI應用與規劃"
    q["subject"] = current_subject
    last_num = q["num"]
all_parsed_questions.extend(raw_11409)

raw_11403 = parse_txt_file(
    os.path.join(TXT_DIR, "iPAS+AI應用規劃師能力鑑定(初級)_樣題(114年3月版).txt"),
    file_type='sample',
    default_year="114年樣題(3月版)",
    default_subject="人工智慧基礎概論"
)
for q in raw_11403:
    if q["num"] >= 16:
        q["subject"] = "生成式AI應用與規劃"
all_parsed_questions.extend(raw_11403)

raw_ref = parse_txt_file(
    os.path.join(TXT_DIR, "iPAS+AI應用規劃師能力鑑定(初級)_樣題參考.txt"),
    file_type='sample',
    default_year="114年樣題參考",
    default_subject="人工智慧基礎概論"
)
for q in raw_ref:
    if q["num"] >= 6:
        q["subject"] = "生成式AI應用與規劃"
all_parsed_questions.extend(raw_ref)

# ==========================================
# 6. 智能去重與合併 + 為每題灌入詳解
# ==========================================
print("\n[去重中] 正在進行智能去重與題目合併...")

unique_questions = []
seen_keys = {}

def clean_text_for_compare(text):
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^\w]", "", text)
    return text

duplicate_count = 0
for q in all_parsed_questions:
    desc_key = clean_text_for_compare(q["desc"])
    
    if not desc_key:
        continue
        
    if desc_key in seen_keys:
        idx = seen_keys[desc_key]
        existing_q = unique_questions[idx]
        
        for opt in ["A", "B", "C", "D"]:
            if not existing_q["options"][opt] and q["options"][opt]:
                existing_q["options"][opt] = q["options"][opt]
                
        if q["year"] not in existing_q["year"]:
            existing_q["year"] += f", {q['year']}"
        if q["source"] not in existing_q["source"]:
            existing_q["source"] += f" / {q['source']}"
            
        duplicate_count += 1
    else:
        seen_keys[desc_key] = len(unique_questions)
        unique_questions.append(q)

print("\n[詳解注入中] 正在呼叫專家知識庫解析器，為每題動態生成詳解...")
for i, q in enumerate(unique_questions):
    q["id"] = f"Q{i+1:03d}"
    if "生成" in q["subject"] or "L12" in q["subject"] or "L22" in q["subject"]:
        q["subject"] = "生成式AI應用與規劃"
    else:
        q["subject"] = "人工智慧基礎概論"
    
    # 呼叫解析引擎
    q["explanation"] = generate_explanation(q)

print(f"[統計] 總共讀入 {len(all_parsed_questions)} 題。")
print(f"[統計] 經智能比對，排除了 {duplicate_count} 題重複題目。")
print(f"[統計] 最終去重後共有 {len(unique_questions)} 題精選考古題！")

os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(unique_questions, f, ensure_ascii=False, indent=2)
print(f"[統計] 含有詳解的題目資料庫已儲存至: {OUTPUT_JSON}")

# ==========================================
# 7. 生成漂亮的 index.html 檔案
# ==========================================
print("\n[建置中] 正在嵌入題目資料庫並生成完美的 HTML 系統中...")

questions_json_str = json.dumps(unique_questions, ensure_ascii=False, indent=2)

html_template = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iPAS AI 應用規劃師 (初級) 歷屆甄試複習系統</title>
    <meta name="description" content="包含 114年、115年人工智慧基礎概論與生成式AI應用與規劃學術甄試題庫。支援模擬考、練習模式、易錯題星號標記、四色答題進度狀態網格，以及去粉紅專業深灰色代碼塊。">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&family=Noto+Sans+TC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #f8fafc;
            --container-bg: #ffffff;
            --text-color: #1e293b;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
            --primary-color: #2563eb;
            --primary-hover: #1d4ed8;
            --success-color: #198754;
            --wrong-color: #dc3545;
            --corrected-color: #f97316;
            --card-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
            --drawer-bg: rgba(255, 255, 255, 0.85);
            --code-bg: #1e293b;
            --code-text: #e2e8f0;
            --tag-bg: #f1f5f9;
            --explanation-bg: #eff6ff;
            --explanation-border: #bfdbfe;
            --explanation-text: #1e3a8a;
        }

        [data-theme="dark"] {
            --bg-color: #0f172a;
            --container-bg: #1e293b;
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --primary-color: #3b82f6;
            --primary-hover: #60a5fa;
            --success-color: #2ec4b6;
            --wrong-color: #ef4444;
            --corrected-color: #fb923c;
            --card-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.3), 0 4px 6px -4px rgb(0 0 0 / 0.3);
            --drawer-bg: rgba(30, 41, 59, 0.85);
            --code-bg: #0f172a;
            --code-text: #f8fafc;
            --tag-bg: #334155;
            --explanation-bg: #1e293b;
            --explanation-border: #3b82f6;
            --explanation-text: #93c5fd;
        }

        [data-theme="sepia"] {
            --bg-color: #f4ecd8;
            --container-bg: #fdf6e3;
            --text-color: #5c4033;
            --text-muted: #8d6e63;
            --border-color: #e6dfcb;
            --primary-color: #8b5a2b;
            --primary-hover: #a0522d;
            --success-color: #2e7d32;
            --wrong-color: #c62828;
            --corrected-color: #ef6c00;
            --card-shadow: 0 4px 6px -1px rgb(92 64 51 / 0.08);
            --drawer-bg: rgba(253, 246, 227, 0.9);
            --code-bg: #3e2723;
            --code-text: #efebe9;
            --tag-bg: #efebe9;
            --explanation-bg: #efebe9;
            --explanation-border: #d7ccc8;
            --explanation-text: #5c4033;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            transition: background-color 0.2s, border-color 0.2s;
        }

        body {
            font-family: 'Outfit', 'Noto Sans TC', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding-bottom: 60px;
        }

        /* V3.4 核心容器尺寸公式 */
        #main-container {
            width: calc(100% - 60px);
            margin: 20px auto;
            max-width: none;
        }

        header {
            background: linear-gradient(135deg, #1e3a8a, #3b82f6);
            color: white;
            padding: 30px 20px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: var(--card-shadow);
            position: relative;
            overflow: hidden;
        }

        header::after {
            content: "";
            position: absolute;
            top: -50%;
            right: -20%;
            width: 300px;
            height: 300px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 50%;
            pointer-events: none;
        }

        header h1 {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }

        header p {
            font-size: 1.05rem;
            opacity: 0.9;
        }

        /* 控制面板 */
        .control-panel {
            background-color: var(--container-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 24px;
            box-shadow: var(--card-shadow);
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            align-items: center;
            justify-content: space-between;
        }

        .filter-group {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
        }

        label {
            font-weight: 600;
            font-size: 0.9rem;
            color: var(--text-muted);
        }

        select, button {
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background-color: var(--container-bg);
            color: var(--text-color);
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            outline: none;
        }

        select:focus {
            border-color: var(--primary-color);
        }

        .tab-btn {
            border: none;
            background-color: transparent;
            padding: 8px 16px;
            border-radius: 6px;
            color: var(--text-muted);
            font-weight: 600;
        }

        .tab-btn.active {
            background-color: var(--primary-color);
            color: white !important;
        }

        .theme-select-container {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* 題目卡片 */
        .question-card {
            background-color: var(--container-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: var(--card-shadow);
            position: relative;
            transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
        }

        /* 焦點引導：藍色外框閃爍 */
        @keyframes flashFocus {
            0% { border-color: var(--primary-color); box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.4); }
            50% { border-color: var(--primary-color); box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.4); }
            100% { border-color: var(--border-color); box-shadow: var(--card-shadow); }
        }

        .question-card.flash-focus {
            animation: flashFocus 1.5s ease-in-out;
        }

        /* 易錯標記狀態邊框 */
        .question-card.flagged {
            border-color: #f97316;
            border-width: 1.5px;
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 8px;
        }

        .tags-container {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }

        .tag {
            background-color: var(--tag-bg);
            color: var(--text-muted);
            font-size: 0.75rem;
            padding: 4px 10px;
            border-radius: 100px;
            font-weight: 500;
        }

        .tag.subject-tag {
            background-color: rgba(37, 99, 235, 0.1);
            color: var(--primary-color);
        }

        .tag.flagged-tag {
            background-color: rgba(249, 115, 22, 0.1);
            color: #f97316;
            display: none;
        }

        .question-card.flagged .tag.flagged-tag {
            display: inline-block;
        }

        .flag-btn {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1.3rem;
            color: #cbd5e1;
            padding: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.15s;
        }

        .flag-btn.active {
            color: #f59e0b;
        }

        .question-desc {
            font-size: 1.05rem;
            font-weight: 500;
            margin-bottom: 20px;
            white-space: pre-wrap;
        }

        /* 去粉紅 code 區塊 (V3.1 規格) */
        pre, code {
            background-color: var(--code-bg) !important;
            color: var(--code-text) !important;
            font-family: 'Consolas', 'Monaco', monospace;
            border-radius: 6px;
        }

        pre {
            padding: 12px 16px;
            margin: 12px 0;
            overflow-x: auto;
            border: 1px solid var(--border-color);
        }

        code {
            padding: 2px 6px;
            font-size: 0.9em;
        }

        /* 選項兩欄式佈局 */
        .options-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 20px;
        }

        @media (max-width: 768px) {
            .options-grid {
                grid-template-columns: 1fr;
            }
        }

        .option-item {
            border: 1px solid var(--border-color);
            background-color: var(--container-bg);
            padding: 14px 18px;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: flex-start;
            gap: 12px;
            font-size: 0.95rem;
            font-weight: 500;
            transition: all 0.15s ease;
        }

        .option-item:hover {
            background-color: var(--tag-bg);
            border-color: var(--primary-color);
        }

        .option-prefix {
            font-weight: 700;
            color: var(--primary-color);
            background-color: rgba(37, 99, 235, 0.08);
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .option-item.selected {
            border-color: var(--primary-color);
            background-color: rgba(37, 99, 235, 0.05);
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
        }

        .option-item.correct {
            border-color: var(--success-color);
            background-color: rgba(25, 135, 84, 0.05);
        }

        .option-item.wrong {
            border-color: var(--wrong-color);
            background-color: rgba(220, 53, 69, 0.05);
        }

        .card-actions {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 16px;
            border-top: 1px solid var(--border-color);
            padding-top: 16px;
        }

        /* V3.1 正確答案條 */
        .answer-bar {
            background-color: #ffffff !important;
            color: #198754 !important;
            border-left: 5px solid #198754 !important;
            padding: 12px 18px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 1.05rem;
            cursor: pointer;
            user-select: none;
            display: none;
            margin-top: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        /* 隱藏答案字體顏色，使其與背景相同 */
        .answer-text {
            color: #ffffff !important;
            transition: color 0.15s;
        }

        /* Hover 時顯現 */
        .answer-bar:hover .answer-text,
        .answer-bar::selection .answer-text {
            color: #198754 !important;
        }

        /* 選取反白時顯現 */
        .answer-text::selection {
            background: rgba(25, 135, 84, 0.15);
            color: #198754 !important;
        }

        /* 詳細解析卡片樣式 */
        .explanation-box {
            background-color: var(--explanation-bg);
            border: 1px solid var(--explanation-border);
            color: var(--text-color);
            padding: 18px;
            border-radius: 12px;
            margin-top: 12px;
            font-size: 0.95rem;
            white-space: pre-wrap;
            display: none;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            line-height: 1.6;
        }

        .reset-btn {
            font-size: 0.85rem;
            padding: 6px 12px;
            border-radius: 6px;
            color: var(--text-muted);
            border-color: var(--border-color);
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .reset-btn:hover {
            background-color: var(--tag-bg);
            color: var(--text-color);
        }

        /* 左側懸浮學習進度導覽側欄 (V3.6 規格) */
        .drawer-handle {
            position: fixed;
            left: 20px;
            bottom: 20px;
            width: 50px;
            height: 50px;
            background-color: var(--primary-color);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            z-index: 1001;
            transition: transform 0.2s;
        }

        .drawer-handle:hover {
            transform: scale(1.1);
        }

        .collapsible-drawer {
            position: fixed;
            left: -320px;
            top: 0;
            width: 320px;
            height: 100vh;
            background-color: var(--drawer-bg);
            backdrop-filter: blur(12px);
            border-right: 1px solid var(--border-color);
            box-shadow: 10px 0 30px rgba(0,0,0,0.15);
            z-index: 1000;
            padding: 24px;
            display: flex;
            flex-direction: column;
            transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .collapsible-drawer.open {
            left: 0;
        }

        .drawer-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
        }

        .drawer-title {
            font-weight: 700;
            font-size: 1.15rem;
        }

        .close-drawer-btn {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1.2rem;
            color: var(--text-muted);
        }

        .stats-dashboard {
            margin-bottom: 24px;
            background-color: rgba(255,255,255,0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 14px;
        }

        .stats-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }

        .stats-val {
            font-weight: 700;
        }

        /* 四色狀態進度網格 */
        .status-matrix-container {
            flex-grow: 1;
            overflow-y: auto;
            margin-bottom: 16px;
        }

        .status-matrix-title {
            font-weight: 600;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 10px;
        }

        .status-matrix {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
        }

        .matrix-cell {
            aspect-ratio: 1;
            border-radius: 8px;
            background-color: #cbd5e1; /* 灰色 Unanswered */
            border: 1px solid rgba(0,0,0,0.05);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.85rem;
            color: white;
            cursor: pointer;
            transition: all 0.15s;
        }

        [data-theme="dark"] .matrix-cell {
            background-color: #475569;
        }

        [data-theme="sepia"] .matrix-cell {
            background-color: #d7ccc8;
            color: #5c4033;
        }

        /* 四色狀態顏色 */
        .matrix-cell.correct {
            background-color: var(--success-color) !important;
            color: white !important;
        }

        .matrix-cell.wrong {
            background-color: var(--wrong-color) !important;
            color: white !important;
        }

        .matrix-cell.corrected {
            background-color: var(--corrected-color) !important;
            color: white !important;
        }

        /* 模擬考區樣式 */
        .exam-section {
            display: none;
        }

        .exam-header-bar {
            background-color: var(--container-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--card-shadow);
        }

        .timer-display {
            font-weight: 700;
            font-size: 1.2rem;
            color: var(--wrong-color);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .exam-score-panel {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            padding: 24px;
            border-radius: 16px;
            margin-bottom: 24px;
            text-align: center;
            display: none;
        }

        .score-num {
            font-size: 3rem;
            font-weight: 800;
            margin: 8px 0;
        }
    </style>
</head>
<body>

<div id="main-container">
    <header>
        <h1>iPAS AI 應用規劃師 (初級) 考古題複習系統</h1>
        <p>完整收錄 114 年與 115 年最新甄試歷屆考題與學術樣題 • 離線極速複習</p>
    </header>

    <!-- 控制面板 -->
    <div class="control-panel">
        <div class="filter-group">
            <button id="tab-practice" class="tab-btn active" onclick="switchView('practice')">📖 平常練習區</button>
            <button id="tab-exam" class="tab-btn" onclick="switchView('exam')">⏱️ 模擬考區</button>
        </div>

        <!-- 練習過濾器 (只在練習區顯示) -->
        <div class="filter-group" id="practice-filters">
            <div>
                <label>年度：</label>
                <select id="filter-year" onchange="filterQuestions()">
                    <option value="all">全部年度</option>
                    <option value="115年第一次">115年 第一次正式試題</option>
                    <option value="114年第四梯次">114年 第四梯次正式試題</option>
                    <option value="114年樣題">114年 歷屆樣題庫</option>
                </select>
            </div>
            <div>
                <label>科目：</label>
                <select id="filter-subject" onchange="filterQuestions()">
                    <option value="all">全部科目</option>
                    <option value="人工智慧基礎概論">人工智慧基礎概論</option>
                    <option value="生成式AI應用與規劃">生成式AI應用與規劃</option>
                </select>
            </div>
            <div>
                <label>顯示：</label>
                <select id="filter-status" onchange="filterQuestions()">
                    <option value="all">全部題目</option>
                    <option value="flagged">僅顯示易錯標記</option>
                </select>
            </div>
        </div>

        <!-- 主題切換與模擬考工具 -->
        <div class="filter-group">
            <div class="theme-select-container">
                <label>主題：</label>
                <select id="theme-select" onchange="changeTheme(this.value)">
                    <option value="light">明亮白</option>
                    <option value="dark">炭極深</option>
                    <option value="sepia">護眼沙</option>
                </select>
            </div>
        </div>
    </div>

    <!-- 模擬考控制面板 -->
    <div class="exam-section" id="exam-controls-bar">
        <div class="exam-header-bar">
            <div>
                <button onclick="startMockExam('exam1')">📝 模擬考卷一</button>
                <button onclick="startMockExam('exam2')">📝 模擬考卷二</button>
                <button onclick="startMockExam('exam3')">📝 隨機考卷 (50題)</button>
            </div>
            <div class="timer-display" id="exam-timer" style="display: none;">
                ⏱️ 剩餘時間: <span id="timer-val">60:00</span>
            </div>
            <div>
                <button id="submit-exam-btn" style="display: none; background-color: var(--success-color); color: white; border: none;" onclick="submitExam()">📤 交卷評分</button>
            </div>
        </div>
        
        <div class="exam-score-panel" id="score-panel">
            <h2>🎉 測驗結束！您的得分</h2>
            <div class="score-num"><span id="score-val">0</span> / 100</div>
            <p>答對題數: <span id="correct-count-val">0</span> / 50 題 | 用時: <span id="time-spent-val">0</span></p>
        </div>
    </div>

    <!-- 主題目容器 -->
    <div id="questions-container">
        <!-- 題目會由 JS 動態渲染 -->
    </div>
</div>

<!-- 左側懸浮側欄 -->
<div class="drawer-handle" onclick="toggleDrawer()">📊</div>
<div class="collapsible-drawer" id="progress-drawer">
    <div class="drawer-header">
        <div class="drawer-title">📈 學習進度追蹤</div>
        <button class="close-drawer-btn" onclick="toggleDrawer()">✕</button>
    </div>
    
    <div class="stats-dashboard">
        <div class="stats-row">
            <span>作答完成度:</span>
            <span class="stats-val" id="progress-percent">0%</span>
        </div>
        <div class="stats-row">
            <span>答對題數 (綠+橘):</span>
            <span class="stats-val" id="stats-correct">0</span>
        </div>
        <div class="stats-row">
            <span>答錯題數 (紅):</span>
            <span class="stats-val" id="stats-wrong">0</span>
        </div>
        <div class="stats-row">
            <span>曾錯已改正 (橘):</span>
            <span class="stats-val" id="stats-corrected">0</span>
        </div>
    </div>
    
    <div class="status-matrix-title">🔘 題號作答狀態矩陣 (點選可跳轉)</div>
    <div class="status-matrix-container">
        <div class="status-matrix" id="drawer-matrix">
            <!-- 題號狀態圓鈕由 JS 動態渲染 -->
        </div>
    </div>
</div>

<script>
    // 嵌入題目資料庫 (含有詳解)
    const dbQuestions = __QUESTIONS_JSON_DATA__;

    // 全域變數
    let currentView = 'practice';
    let flaggedQuestions = JSON.parse(localStorage.getItem('flagged_questions')) || [];
    let practiceHistory = JSON.parse(localStorage.getItem('practice_history')) || {};
    let currentTheme = localStorage.getItem('review_system_theme') || 'light';
    
    // 模擬考狀態
    let examActive = false;
    let examQuestions = [];
    let examAnswers = {};
    let examTimerInterval = null;
    let examTimeLimit = 3600; // 60 mins

    // 初始化
    document.addEventListener("DOMContentLoaded", () => {
        changeTheme(currentTheme);
        document.getElementById('theme-select').value = currentTheme;
        
        // 預設渲染平常練習區
        renderPracticeArea();
        updateDrawerStats();
    });

    // 切換頁面視圖
    function switchView(view) {
        currentView = view;
        document.getElementById('tab-practice').classList.toggle('active', view === 'practice');
        document.getElementById('tab-exam').classList.toggle('active', view === 'exam');
        document.getElementById('practice-filters').style.display = view === 'practice' ? 'flex' : 'none';
        document.getElementById('exam-controls-bar').style.display = view === 'exam' ? 'block' : 'none';
        
        if (examTimerInterval) {
            clearInterval(examTimerInterval);
        }
        document.getElementById('exam-timer').style.display = 'none';
        document.getElementById('submit-exam-btn').style.display = 'none';
        document.getElementById('score-panel').style.display = 'none';
        examActive = false;

        if (view === 'practice') {
            renderPracticeArea();
        } else {
            document.getElementById('questions-container').innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <h2>⏱️ 歡迎進入模擬考區</h2>
                    <p style="margin-top: 10px;">請點選上方「模擬考卷一」、「二」或「隨機考卷」開始測驗。</p>
                </div>
            `;
        }
        updateDrawerStats();
    }

    // 主題變更
    function changeTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('review_system_theme', theme);
    }

    // 側邊欄開關
    function toggleDrawer() {
        document.getElementById('progress-drawer').classList.toggle('open');
    }

    // 平常練習區過濾與渲染
    function renderPracticeArea() {
        const yearFilter = document.getElementById('filter-year').value;
        const subjectFilter = document.getElementById('filter-subject').value;
        const statusFilter = document.getElementById('filter-status').value;
        
        let filtered = dbQuestions;

        // 年度過濾
        if (yearFilter !== 'all') {
            if (yearFilter === '114年樣題') {
                filtered = filtered.filter(q => q.year.includes('樣題'));
            } else {
                filtered = filtered.filter(q => q.year.includes(yearFilter));
            }
        }
        
        // 科目過濾
        if (subjectFilter !== 'all') {
            filtered = filtered.filter(q => q.subject === subjectFilter);
        }

        // 標記過濾
        if (statusFilter === 'flagged') {
            filtered = filtered.filter(q => flaggedQuestions.includes(q.id));
        }

        renderQuestions(filtered, false);
    }

    function filterQuestions() {
        if (currentView === 'practice') {
            renderPracticeArea();
            updateDrawerStats();
        }
    }

    // 渲染題目卡片
    function renderQuestions(questions, isExamMode) {
        const container = document.getElementById('questions-container');
        if (questions.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <h2>無符合條件的題目</h2>
                </div>
            `;
            return;
        }

        container.innerHTML = questions.map((q, idx) => {
            const isFlagged = flaggedQuestions.includes(q.id);
            const history = practiceHistory[q.id] || {};
            const isAnswered = history.status !== undefined;
            
            // 決定選項樣式
            let optAClass = "", optBClass = "", optCClass = "", optDClass = "";
            let showAnswer = false;

            if (!isExamMode && isAnswered) {
                showAnswer = true;
                const chosen = history.chosen;
                const correct = q.answer;
                
                // 標示對錯
                if (chosen === 'A') optAClass = (correct === 'A') ? 'correct' : 'wrong';
                if (chosen === 'B') optBClass = (correct === 'B') ? 'correct' : 'wrong';
                if (chosen === 'C') optCClass = (correct === 'C') ? 'correct' : 'wrong';
                if (chosen === 'D') optDClass = (correct === 'D') ? 'correct' : 'wrong';
                
                // 正確答案高亮
                if (correct === 'A') optAClass = 'correct';
                if (correct === 'B') optBClass = 'correct';
                if (correct === 'C') optCClass = 'correct';
                if (correct === 'D') optDClass = 'correct';
            } else if (isExamMode) {
                // 模擬考模式，高亮點選的選項，但不顯示正誤
                const chosen = examAnswers[q.id];
                if (chosen === 'A') optAClass = 'selected';
                if (chosen === 'B') optBClass = 'selected';
                if (chosen === 'C') optCClass = 'selected';
                if (chosen === 'D') optDClass = 'selected';
            }

            // 處理 HTML 安全字元
            let displayDesc = q.desc;
            displayDesc = displayDesc.replace(/</g, "&lt;").replace(/>/g, "&gt;");

            // 特殊渲染程式碼片段 (V3.1 去粉紅代碼規格)
            if (displayDesc.includes("#include") || displayDesc.includes("int main") || displayDesc.includes("using namespace") || displayDesc.includes("def ") || displayDesc.includes("class ")) {
                const lines = displayDesc.split("\\n");
                let normalText = "";
                let codeText = "";
                let inCode = false;
                
                lines.forEach(l => {
                    if (l.includes("#include") || l.includes("using ") || l.includes("int ") || l.includes("void ") || l.includes("{") || l.includes("}") || l.includes("cout") || l.includes("std::")) {
                        inCode = true;
                    }
                    if (inCode) {
                        codeText += l + "\\n";
                    } else {
                        normalText += l + "\\n";
                    }
                });
                
                if (codeText) {
                    displayDesc = normalText.trim() + `<pre><code>${codeText.trim()}</code></pre>`;
                }
            }

            return `
                <div class="question-card ${isFlagged ? 'flagged' : ''}" id="card-${q.id}">
                    <div class="card-header">
                        <div class="tags-container">
                            <span class="tag"># ${idx + 1}</span>
                            <span class="tag subject-tag">${q.subject}</span>
                            <span class="tag">${q.year}</span>
                            <span class="tag flagged-tag">易錯題</span>
                        </div>
                        <button class="flag-btn ${isFlagged ? 'active' : ''}" onclick="toggleFlag('${q.id}')">★</button>
                    </div>
                    
                    <div class="question-desc">${displayDesc}</div>
                    
                    <div class="options-grid">
                        <div class="option-item ${optAClass}" onclick="selectOption(this, '${q.id}', 'A', ${isExamMode})">
                            <span class="option-prefix">A</span>
                            <span>${q.options.A.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</span>
                        </div>
                        <div class="option-item ${optBClass}" onclick="selectOption(this, '${q.id}', 'B', ${isExamMode})">
                            <span class="option-prefix">B</span>
                            <span>${q.options.B.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</span>
                        </div>
                        <div class="option-item ${optCClass}" onclick="selectOption(this, '${q.id}', 'C', ${isExamMode})">
                            <span class="option-prefix">C</span>
                            <span>${q.options.C.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</span>
                        </div>
                        <div class="option-item ${optDClass}" onclick="selectOption(this, '${q.id}', 'D', ${isExamMode})">
                            <span class="option-prefix">D</span>
                            <span>${q.options.D.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</span>
                        </div>
                    </div>
                    
                    ${!isExamMode ? `
                        <div class="answer-bar" id="ans-${q.id}" style="display: ${showAnswer ? 'block' : 'none'}">
                            💡 正確答案：<span class="answer-text">${q.answer}</span>
                            <p style="font-size: 0.85rem; font-weight: normal; margin-top: 6px; color: var(--text-muted);">
                                (滑鼠指針移入上方綠色區域或反白可顯示答案字母)
                            </p>
                        </div>
                        
                        <div class="explanation-box" id="exp-${q.id}" style="display: ${showAnswer ? 'block' : 'none'}">
                            ${q.explanation}
                        </div>

                        <div class="card-actions">
                            <button class="reset-btn" onclick="resetQuestion('${q.id}')">🔄 重新作答</button>
                            <span style="font-size: 0.8rem; color: var(--text-muted);">資料來源: ${q.source}</span>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    // 易錯旗標切換
    function toggleFlag(qId) {
        const card = document.getElementById(`card-${qId}`);
        const btn = card ? card.querySelector('.flag-btn') : null;
        
        if (flaggedQuestions.includes(qId)) {
            flaggedQuestions = flaggedQuestions.filter(id => id !== qId);
            if (card) card.classList.remove('flagged');
            if (btn) btn.classList.remove('active');
        } else {
            flaggedQuestions.push(qId);
            if (card) card.classList.add('flagged');
            if (btn) btn.classList.add('active');
        }
        
        localStorage.setItem('flagged_questions', JSON.stringify(flaggedQuestions));
        
        if (document.getElementById('filter-status').value === 'flagged') {
            renderPracticeArea();
        }
    }

    // 作答選項點選 (V3.5 DOM 相對定位高亮規格)
    function selectOption(elem, qId, optionChar, isExamMode) {
        const card = elem.closest('.question-card');
        const grid = elem.closest('.options-grid');
        
        const q = dbQuestions.find(item => item.id === qId);
        if (!q) return;

        if (isExamMode) {
            grid.querySelectorAll('.option-item').forEach(el => el.classList.remove('selected'));
            elem.classList.add('selected');
            examAnswers[qId] = optionChar;
            
            updateDrawerStats();
            return;
        }

        const history = practiceHistory[qId] || {};
        if (history.status !== undefined) {
            return;
        }

        const isCorrect = (q.answer === optionChar);
        let newStatus = 'unanswered';
        
        grid.querySelectorAll('.option-item').forEach(el => el.classList.remove('correct', 'wrong'));
        
        if (isCorrect) {
            elem.classList.add('correct');
            if (history.has_wrong) {
                newStatus = 'corrected';
            } else {
                newStatus = 'correct';
            }
        } else {
            elem.classList.add('wrong');
            newStatus = 'wrong';
            const opts = grid.querySelectorAll('.option-item');
            const mapChar = { 'A':0, 'B':1, 'C':2, 'D':3 };
            opts[mapChar[q.answer]].classList.add('correct');
        }

        // 顯示正確答案條與詳細解析卡片
        const ansBar = card.querySelector('.answer-bar');
        if (ansBar) ansBar.style.display = 'block';

        const expBox = card.querySelector('.explanation-box');
        if (expBox) expBox.style.display = 'block';

        practiceHistory[qId] = {
            status: newStatus,
            chosen: optionChar,
            has_wrong: history.has_wrong || !isCorrect
        };
        localStorage.setItem('practice_history', JSON.stringify(practiceHistory));

        updateDrawerStats();
    }

    // 重新作答機制
    function resetQuestion(qId) {
        const card = document.getElementById(`card-${qId}`);
        if (!card) return;

        card.querySelectorAll('.option-item').forEach(el => {
            el.classList.remove('correct', 'wrong', 'selected');
        });

        // 隱藏正確答案與詳細解析
        const ansBar = card.querySelector('.answer-bar');
        if (ansBar) ansBar.style.display = 'none';

        const expBox = card.querySelector('.explanation-box');
        if (expBox) expBox.style.display = 'none';

        const history = practiceHistory[qId] || {};
        if (history.status) {
            practiceHistory[qId] = {
                has_wrong: history.has_wrong || (history.status === 'wrong')
            };
        }
        localStorage.setItem('practice_history', JSON.stringify(practiceHistory));
        
        updateDrawerStats();
    }

    // 更新學習進度與渲染側欄四色進度網格
    function updateDrawerStats() {
        let listToRender = [];
        if (currentView === 'practice') {
            const yearFilter = document.getElementById('filter-year').value;
            const subjectFilter = document.getElementById('filter-subject').value;
            const statusFilter = document.getElementById('filter-status').value;
            
            listToRender = dbQuestions;
            if (yearFilter !== 'all') {
                if (yearFilter === '114年樣題') {
                    listToRender = listToRender.filter(q => q.year.includes('樣題'));
                } else {
                    listToRender = listToRender.filter(q => q.year.includes(yearFilter));
                }
            }
            if (subjectFilter !== 'all') {
                listToRender = listToRender.filter(q => q.subject === subjectFilter);
            }
            if (statusFilter === 'flagged') {
                listToRender = listToRender.filter(q => flaggedQuestions.includes(q.id));
            }
        } else {
            listToRender = examQuestions;
        }

        let answeredCount = 0;
        let correctCount = 0;
        let wrongCount = 0;
        let correctedCount = 0;

        const matrixContainer = document.getElementById('drawer-matrix');
        matrixContainer.innerHTML = listToRender.map((q, idx) => {
            const history = practiceHistory[q.id] || {};
            let cellClass = 'unanswered';
            
            if (currentView === 'exam') {
                if (examAnswers[q.id]) {
                    cellClass = 'correct'; 
                }
            } else {
                if (history.status === 'correct') {
                    cellClass = 'correct';
                    correctCount++;
                    answeredCount++;
                } else if (history.status === 'wrong') {
                    cellClass = 'wrong';
                    wrongCount++;
                    answeredCount++;
                } else if (history.status === 'corrected') {
                    cellClass = 'corrected';
                    correctedCount++;
                    answeredCount++;
                }
            }

            return `<div class="matrix-cell ${cellClass}" onclick="jumpToQuestion('${q.id}')">${idx + 1}</div>`;
        }).join('');

        const total = listToRender.length;
        if (total > 0) {
            const percent = currentView === 'exam' 
                ? Math.round((Object.keys(examAnswers).length / total) * 100)
                : Math.round((answeredCount / total) * 100);
            document.getElementById('progress-percent').innerText = `${percent}%`;
            
            if (currentView === 'practice') {
                document.getElementById('stats-correct').innerText = correctCount + correctedCount;
                document.getElementById('stats-wrong').innerText = wrongCount;
                document.getElementById('stats-corrected').innerText = correctedCount;
            } else {
                document.getElementById('stats-correct').innerText = Object.keys(examAnswers).length;
                document.getElementById('stats-wrong').innerText = total - Object.keys(examAnswers).length;
                document.getElementById('stats-corrected').innerText = "0";
            }
        } else {
            document.getElementById('progress-percent').innerText = "0%";
            document.getElementById('stats-correct').innerText = "0";
            document.getElementById('stats-wrong').innerText = "0";
            document.getElementById('stats-corrected').innerText = "0";
        }
    }

    // 平滑跳轉與焦點引導閃爍
    function jumpToQuestion(qId) {
        const card = document.getElementById(`card-${qId}`);
        if (!card) return;

        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        if (window.innerWidth < 768) {
            toggleDrawer();
        }

        card.classList.remove('flash-focus');
        void card.offsetWidth; 
        card.classList.add('flash-focus');
        
        setTimeout(() => {
            card.classList.remove('flash-focus');
        }, 1500);
    }

    // ==========================================
    // 模擬考區核心邏輯
    // ==========================================
    function startMockExam(examType) {
        if (examActive) {
            if (!confirm('目前有正在進行中的模擬考，確定要重新開始並放棄目前成績嗎？')) {
                return;
            }
        }

        examActive = true;
        examAnswers = {};
        document.getElementById('score-panel').style.display = 'none';

        const subject1 = dbQuestions.filter(q => q.subject === '人工智慧基礎概論');
        const subject2 = dbQuestions.filter(q => q.subject === '生成式AI應用與規劃');

        let seed = Math.random();
        if (examType === 'exam1') {
            seed = 0.12345;
        } else if (examType === 'exam2') {
            seed = 0.67890;
        }

        examQuestions = [
            ...getRandomSubarray(subject1, 25, seed),
            ...getRandomSubarray(subject2, 25, seed + 0.1)
        ];

        renderQuestions(examQuestions, true);
        
        let timeLeft = examTimeLimit;
        document.getElementById('exam-timer').style.display = 'flex';
        document.getElementById('submit-exam-btn').style.display = 'inline-block';
        
        if (examTimerInterval) clearInterval(examTimerInterval);
        
        updateTimerDisplay(timeLeft);
        examTimerInterval = setInterval(() => {
            timeLeft--;
            updateTimerDisplay(timeLeft);
            if (timeLeft <= 0) {
                clearInterval(examTimerInterval);
                alert('時間到！系統將自動交卷。');
                submitExam();
            }
        }, 1000);

        updateDrawerStats();
    }

    function getRandomSubarray(arr, size, seed) {
        let shuffled = arr.slice(0);
        let m = 0x80000000; 
        let a = 1103515245;
        let c = 12345;
        let state = Math.round(seed * m);
        
        function nextRandom() {
            state = (a * state + c) % m;
            return state / m;
        }

        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(nextRandom() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled.slice(0, size);
    }

    function updateTimerDisplay(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        document.getElementById('timer-val').innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    function submitExam() {
        if (!examActive) return;
        
        clearInterval(examTimerInterval);
        examActive = false;
        
        document.getElementById('exam-timer').style.display = 'none';
        document.getElementById('submit-exam-btn').style.display = 'none';

        let correctCount = 0;
        examQuestions.forEach(q => {
            const chosen = examAnswers[q.id];
            if (chosen === q.answer) {
                correctCount++;
            }
        });

        const score = Math.round((correctCount / examQuestions.length) * 100);
        
        document.getElementById('score-panel').style.display = 'block';
        document.getElementById('score-val').innerText = score;
        document.getElementById('correct-count-val').innerText = correctCount;
        
        const timeSpent = examTimeLimit - parseTimeRemaining();
        const spentMins = Math.floor(timeSpent / 60);
        const spentSecs = timeSpent % 60;
        document.getElementById('time-spent-val').innerText = `${spentMins}分${spentSecs}秒`;

        renderExamResults();
    }

    function parseTimeRemaining() {
        const val = document.getElementById('timer-val').innerText.split(':');
        return parseInt(val[0]) * 60 + parseInt(val[1]);
    }

    function renderExamResults() {
        const container = document.getElementById('questions-container');
        container.innerHTML = examQuestions.map((q, idx) => {
            const chosen = examAnswers[q.id];
            const correct = q.answer;
            const isCorrect = (chosen === correct);
            const isFlagged = flaggedQuestions.includes(q.id);

            let optAClass = "", optBClass = "", optCClass = "", optDClass = "";
            if (chosen === 'A') optAClass = isCorrect ? 'correct' : 'wrong';
            if (chosen === 'B') optBClass = isCorrect ? 'correct' : 'wrong';
            if (chosen === 'C') optCClass = isCorrect ? 'correct' : 'wrong';
            if (chosen === 'D') optDClass = isCorrect ? 'correct' : 'wrong';

            if (correct === 'A') optAClass = 'correct';
            if (correct === 'B') optBClass = 'correct';
            if (correct === 'C') optCClass = 'correct';
            if (correct === 'D') optDClass = 'correct';

            let displayDesc = q.desc.replace(/</g, "&lt;").replace(/>/g, "&gt;");

            return `
                <div class="question-card ${isFlagged ? 'flagged' : ''} ${isCorrect ? 'correct-border' : 'wrong-border'}" id="card-${q.id}">
                    <div class="card-header">
                        <div class="tags-container">
                            <span class="tag"># ${idx + 1}</span>
                            <span class="tag subject-tag">${q.subject}</span>
                            <span class="tag">${q.year}</span>
                            <span class="tag" style="background-color: ${isCorrect ? 'rgba(25, 135, 84, 0.1)' : 'rgba(220, 53, 69, 0.1)'}; color: ${isCorrect ? 'var(--success-color)' : 'var(--wrong-color)'};">
                                ${isCorrect ? '🟩 答對' : `🟥 答錯 (您選: ${chosen || '未答'})`}
                            </span>
                        </div>
                        <button class="flag-btn ${isFlagged ? 'active' : ''}" onclick="toggleFlag('${q.id}')">★</button>
                    </div>
                    
                    <div class="question-desc">${displayDesc}</div>
                    
                    <div class="options-grid">
                        <div class="option-item ${optAClass}">
                            <span class="option-prefix">A</span>
                            <span>${q.options.A.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</span>
                        </div>
                        <div class="option-item ${optBClass}">
                            <span class="option-prefix">B</span>
                            <span>${q.options.B.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</span>
                        </div>
                        <div class="option-item ${optCClass}">
                            <span class="option-prefix">C</span>
                            <span>${q.options.C.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</span>
                        </div>
                        <div class="option-item ${optDClass}">
                            <span class="option-prefix">D</span>
                            <span>${q.options.D.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</span>
                        </div>
                    </div>
                    
                    <div class="answer-bar" id="ans-${q.id}" style="display: block;">
                        💡 正確答案：<span class="answer-text">${q.answer}</span>
                        <p style="font-size: 0.85rem; font-weight: normal; margin-top: 6px; color: var(--text-muted);">
                            (滑鼠指針移入上方綠色區域或反白可顯示答案字母)
                        </p>
                    </div>

                    <div class="explanation-box" id="exp-${q.id}" style="display: block;">
                        ${q.explanation}
                    </div>
                </div>
            `;
        }).join('');
        
        updateDrawerStats();
    }
</script>
</body>
</html>
"""

# 取代題目 JSON
html_content = html_template.replace("__QUESTIONS_JSON_DATA__", questions_json_str)

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\n[生成成功] 順利生成全新的 iPAS 考古題複習系統網頁(含大綱詳解): {OUTPUT_HTML}")
print("[完成] 考古題複習系統一鍵生成完畢！請直接在瀏覽器中雙擊打開 index.html 進行練習！")
print("==================================================")
