// 完整的留学申请指南内容数据
const guideContent = {
    part1: {
        title: "第一部分：通用申请流程",
        description: "了解留学申请的基本流程和核心要素",
        sections: [
            {
                id: "section1-1",
                title: "1. 留学申请时间轴和规划",
                icon: "fas fa-calendar-alt",
                content: `
                    <p class="mb-4">留学申请是一个长期的过程，通常建议提前1.5-2年开始规划。一个清晰的时间轴能帮助你从容不迫地完成各项准备。</p>
                    
                    <div class="bg-blue-50 p-4 sm:p-6 rounded-lg mb-6">
                        <h4 class="font-bold text-primary-800 mb-3">以申请秋季入学为例（例如2026年9月入学）：</h4>
                        
                        <div class="space-y-4 sm:space-y-6">
                            <div class="border-l-4 border-yellow-400 pl-4">
                                <h5 class="font-semibold text-gray-900 mb-2">申请前一年（2025年1月 - 6月）：信息搜集与自我定位</h5>
                                <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm sm:text-base">
                                    <li><strong>1月-3月：</strong> 初步了解留学国家、院校和专业，明确自己的兴趣和方向。开始收集相关资料，参加教育展。</li>
                                    <li><strong>4月-6月：</strong> 保持并提升在校GPA成绩。开始准备语言考试（托福/雅思），背单词、练听力。了解标准化考试（SAT/ACT）要求。</li>
                                </ul>
                            </div>
                            
                            <div class="border-l-4 border-orange-400 pl-4">
                                <h5 class="font-semibold text-gray-900 mb-2">申请前一年（2025年7月 - 12月）：背景提升与考试准备</h5>
                                <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm sm:text-base">
                                    <li><strong>7月-8月（暑假）：</strong> 参加语言考试或标准化考试的培训课程。参与科研、实习、夏校、志愿者等背景提升项目。</li>
                                    <li><strong>9月-10月：</strong> 进行第一次语言考试。根据成绩决定是否需要再次报考。开始构思个人陈述的框架和内容。</li>
                                    <li><strong>11月-12月：</strong> 最终确定目标院校名单，分为"冲刺"、"匹配"、"保底"三档。联系推荐人，沟通推荐信事宜。</li>
                                </ul>
                            </div>
                            
                            <div class="border-l-4 border-green-400 pl-4">
                                <h5 class="font-semibold text-gray-900 mb-2">申请当年（2026年1月 - 6月）：申请材料冲刺与准备</h5>
                                <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm sm:text-base">
                                    <li><strong>1月-3月：</strong> 完成个人陈述、简历等核心文书的初稿。将文书交由老师、顾问或专业人士审阅并修改。</li>
                                    <li><strong>4月-6月：</strong> 准备所有申请材料，包括成绩单、在读证明、存款证明、护照等。</li>
                                </ul>
                            </div>
                            
                            <div class="border-l-4 border-blue-400 pl-4">
                                <h5 class="font-semibold text-gray-900 mb-2">申请当年（2026年7月 - 12月）：申请提交与等待</h5>
                                <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm sm:text-base">
                                    <li><strong>8月-9月：</strong> 填写网申表格，如美国的Common Application系统会于8月1日开放。上传所有申请材料，支付申请费。</li>
                                    <li><strong>10月-12月：</strong> 密切关注申请截止日期，尤其是"早申请"的截止日期通常在11月1日或11月15日。</li>
                                </ul>
                            </div>
                            
                            <div class="border-l-4 border-purple-400 pl-4">
                                <h5 class="font-semibold text-gray-900 mb-2">录取后（2027年1月 - 8月）：录取与行前准备</h5>
                                <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm sm:text-base">
                                    <li><strong>1月-4月：</strong> 陆续收到录取结果（Offer）。仔细比较不同学校的优劣，做出最终决定。</li>
                                    <li><strong>5月-6月：</strong> 接受心仪学校的Offer，并按要求支付入学押金。申请学生宿舍。</li>
                                    <li><strong>6月-7月：</strong> 准备签证申请材料，并递交签证申请。</li>
                                    <li><strong>8月：</strong> 预订机票，安排接机，打包行李，做好充分的行前准备。</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                        <h4 class="font-bold text-yellow-800 mb-2">关键提示：</h4>
                        <ul class="list-disc list-inside space-y-1 text-yellow-700 text-sm sm:text-base">
                            <li><strong>尽早开始</strong>：准备工作越早，时间越充裕，越能从容应对。</li>
                            <li><strong>个性化调整</strong>：以上时间线为通用模板，需根据目标国家、学校及个人情况灵活调整。</li>
                            <li><strong>关注截止日期</strong>：牢记各个学校和申请系统的关键截止日期，避免错失良机。</li>
                        </ul>
                    </div>
                `
            },
            {
                id: "section1-2",
                title: "2. 学术成绩准备",
                icon: "fas fa-chart-line",
                content: `
                    <p class="mb-4">学术成绩是留学申请中最为核心的硬件条件，直接反映了申请者的学习能力和知识储备。优秀的学术背景是敲开名校大门的关键。</p>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 mb-6">
                        <div class="bg-blue-50 p-4 sm:p-6 rounded-lg">
                            <h4 class="font-bold text-blue-800 mb-3">1. 在校平均成绩（GPA）</h4>
                            <ul class="space-y-2 text-sm text-blue-700">
                                <li><strong>重要性：</strong>GPA是招生官评估你学术能力最直观、最重要的指标</li>
                                <li><strong>计算方式：</strong>需按照目标院校的要求进行换算和提交</li>
                                <li><strong>提升策略：</strong>认真对待每一门课程，保持上升趋势</li>
                            </ul>
                        </div>
                        
                        <div class="bg-green-50 p-4 sm:p-6 rounded-lg">
                            <h4 class="font-bold text-green-800 mb-3">2. 选修课程与学术挑战</h4>
                            <ul class="space-y-2 text-sm text-green-700">
                                <li><strong>课程选择：</strong>选择与申请专业相关的选修课程</li>
                                <li><strong>学术竞赛：</strong>参加权威的学术竞赛，展示学术热情</li>
                                <li><strong>科研项目：</strong>参与科研项目或撰写学术论文</li>
                            </ul>
                        </div>
                        
                        <div class="bg-purple-50 p-4 sm:p-6 rounded-lg">
                            <h4 class="font-bold text-purple-800 mb-3">3. 标准化课程体系</h4>
                            <ul class="space-y-2 text-sm text-purple-700">
                                <li><strong>AP课程：</strong>Advanced Placement，美国大学预修课程</li>
                                <li><strong>IB课程：</strong>International Baccalaureate，国际文凭课程</li>
                                <li><strong>A-Level：</strong>英国高中课程，被全球广泛认可</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="bg-red-50 border border-red-200 p-4 rounded-lg">
                        <h4 class="font-bold text-red-800 mb-2">关键提示：</h4>
                        <ul class="list-disc list-inside space-y-1 text-red-700 text-sm sm:text-base">
                            <li><strong>真实性</strong>：所有提交的学术材料必须真实有效，任何形式的作假行为都会导致申请失败</li>
                            <li><strong>长期努力</strong>：学术背景的提升非一日之功，需要从进入高中开始就持之以恒地努力</li>
                        </ul>
                    </div>
                `
            },
            {
                id: "section1-3",
                title: "3. 语言考试准备（托福/雅思等）",
                icon: "fas fa-language",
                content: `
                    <p class="mb-6">对于母语非英语的学生来说，语言水平是必须跨过的一道门槛。绝大多数英语授课的大学都会要求申请者提供标准化的英语考试成绩。</p>
                    
                    <div class="overflow-x-auto mb-6">
                        <table class="w-full border-collapse border border-gray-300 min-w-full text-sm">
                            <thead>
                                <tr class="bg-gray-100">
                                    <th class="border border-gray-300 px-2 sm:px-4 py-2 text-left">特点</th>
                                    <th class="border border-gray-300 px-2 sm:px-4 py-2 text-left">托福 (TOEFL iBT)</th>
                                    <th class="border border-gray-300 px-2 sm:px-4 py-2 text-left">雅思 (IELTS Academic)</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2 font-semibold">主办方</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">美国教育考试服务中心 (ETS)</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">英国文化协会、IDP、剑桥大学考试委员会</td>
                                </tr>
                                <tr class="bg-gray-50">
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2 font-semibold">主要适用</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">北美院校（美国、加拿大）</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">英联邦国家（英国、澳大利亚、新西兰）</td>
                                </tr>
                                <tr>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2 font-semibold">评分体系</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">总分120分（听说读写各30分）</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">总分9.0分（听说读写各9.0分，取平均值）</td>
                                </tr>
                                <tr class="bg-gray-50">
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2 font-semibold">考试形式</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">全程机考（听说读写）</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">纸笔考试 或 机考，口语为人人对话</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-4 sm:p-6 rounded-lg">
                            <h4 class="font-bold text-blue-800 mb-3">如何选择？</h4>
                            <ul class="space-y-2 text-blue-700 text-sm">
                                <li><strong>目标国家：</strong>主要申请美国大学建议首选托福；主要申请英联邦国家建议首选雅思</li>
                                <li><strong>考试模式偏好：</strong>更适应电脑考试选择托福；更喜欢传统纸笔作答选择雅思</li>
                                <li><strong>个人能力：</strong>可以分别尝试两种考试的模拟题，看哪种更能发挥优势</li>
                            </ul>
                        </div>
                        
                        <div class="bg-green-50 p-4 sm:p-6 rounded-lg">
                            <h4 class="font-bold text-green-800 mb-3">备考策略</h4>
                            <ul class="space-y-2 text-green-700 text-sm">
                                <li><strong>词汇是基础：</strong>充足的学术词汇量都是取得高分的基石</li>
                                <li><strong>分项突破：</strong>针对听说读写四个单项进行专项训练</li>
                                <li><strong>刷题与模考：</strong>通过大量练习官方真题来熟悉考试节奏和题型</li>
                                <li><strong>寻求专业帮助：</strong>如果自学效果不佳，考虑参加培训班</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                        <h4 class="font-bold text-yellow-800 mb-2">关键提示：</h4>
                        <ul class="list-disc list-inside space-y-1 text-yellow-700 text-sm sm:text-base">
                            <li><strong>尽早报名</strong>：考位有限，尤其在考试高峰期，建议提前2-3个月报名锁定考位</li>
                            <li><strong>成绩有效期</strong>：托福和雅思成绩的有效期均为2年，请确保在申请时成绩依然有效</li>
                            <li><strong>送分</strong>：部分学校要求由考试机构官方寄送成绩单，务必提前了解学校要求并完成送分操作</li>
                        </ul>
                    </div>
                `
            },
            {
                id: "section1-4",
                title: "4. 标准化考试（SAT/ACT等）",
                icon: "fas fa-pencil-alt",
                content: `
                    <p class="mb-6">除了语言考试，部分国家（主要是美国）的顶尖大学还会建议或要求申请者提供标准化考试成绩，作为评估学术能力的另一项重要参考。</p>
                    
                    <div class="overflow-x-auto mb-6">
                        <table class="w-full border-collapse border border-gray-300 min-w-full text-sm">
                            <thead>
                                <tr class="bg-gray-100">
                                    <th class="border border-gray-300 px-2 sm:px-4 py-2 text-left">特点</th>
                                    <th class="border border-gray-300 px-2 sm:px-4 py-2 text-left">SAT</th>
                                    <th class="border border-gray-300 px-2 sm:px-4 py-2 text-left">ACT</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2 font-semibold">考察重点</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">逻辑思维与分析推理能力</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">学科知识掌握与快速解题能力</td>
                                </tr>
                                <tr class="bg-gray-50">
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2 font-semibold">科目构成</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">阅读与文法、数学</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">英语、数学、阅读、科学，外加可选的写作</td>
                                </tr>
                                <tr>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2 font-semibold">考试节奏</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">每道题的平均时间相对宽裕</td>
                                    <td class="border border-gray-300 px-2 sm:px-4 py-2">节奏更快，要求更高的解题速度</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-4 sm:p-6 rounded-lg">
                            <h4 class="font-bold text-blue-800 mb-3">是否需要参加？</h4>
                            <ul class="space-y-2 text-blue-700 text-sm">
                                <li><strong>Test-Optional政策：</strong>许多美国大学采取"考试可选"政策</li>
                                <li><strong>院校要求：</strong>顶尖院校仍然建议提交成绩</li>
                                <li><strong>国际学生：</strong>有竞争力的成绩是强有力的加分项</li>
                            </ul>
                        </div>
                        
                        <div class="bg-green-50 p-4 sm:p-6 rounded-lg">
                            <h4 class="font-bold text-green-800 mb-3">备考建议</h4>
                            <ul class="space-y-2 text-green-700 text-sm">
                                <li><strong>做模考题：</strong>分别尝试SAT和ACT模考题</li>
                                <li><strong>发挥优势：</strong>根据个人能力选择合适的考试</li>
                                <li><strong>系统备考：</strong>背单词、分项练习、刷真题</li>
                            </ul>
                        </div>
                    </div>
                `
            },
            {
                id: "section1-5",
                title: "5. 申请材料准备（个人陈述、推荐信等）",
                icon: "fas fa-file-alt",
                content: `
                    <p class="mb-6">如果说GPA和标化考试成绩是申请的"硬件"，那么申请材料就是展示你个性、才华和潜力的"软件"。</p>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                        <div class="bg-blue-50 p-6 rounded-lg">
                            <h4 class="font-bold text-blue-800 mb-3">个人陈述 (PS)</h4>
                            <ul class="space-y-2 text-sm text-blue-700">
                                <li><strong>独特性：</strong>写你自己的故事，避免模板化</li>
                                <li><strong>真诚性：</strong>情感要真实，经历要可信</li>
                                <li><strong>逻辑性：</strong>结构清晰，围绕核心主题</li>
                            </ul>
                        </div>
                        
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold text-green-800 mb-3">推荐信 (RL)</h4>
                            <ul class="space-y-2 text-sm text-green-700">
                                <li><strong>选择推荐人：</strong>选择真正了解你的老师</li>
                                <li><strong>相关性：</strong>最好是专业相关的科目老师</li>
                                <li><strong>提前沟通：</strong>至少提前1-2个月联系</li>
                            </ul>
                        </div>
                        
                        <div class="bg-purple-50 p-6 rounded-lg">
                            <h4 class="font-bold text-purple-800 mb-3">简历 (CV)</h4>
                            <ul class="space-y-2 text-sm text-purple-700">
                                <li><strong>格式要求：</strong>通常建议在一页以内</li>
                                <li><strong>内容要点：</strong>教育背景、活动经历、奖项</li>
                                <li><strong>突出重点：</strong>用动词开头描述成果</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                        <h4 class="font-bold text-yellow-800 mb-2">关键提示：</h4>
                        <ul class="list-disc list-inside space-y-1 text-yellow-700 text-sm sm:text-base">
                            <li><strong>整体性</strong>：所有申请材料应该是一个有机的整体</li>
                            <li><strong>细节决定成败</strong>：仔细检查格式、拼写和语法错误</li>
                        </ul>
                    </div>
                `
            },
            {
                id: "section1-6",
                title: "6. 选校策略",
                icon: "fas fa-search",
                content: `
                    <p class="mb-6">选校是整个留学申请过程中至关重要的一环，它直接决定了你未来几年的学习和生活环境。</p>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-6 rounded-lg">
                            <h4 class="font-bold text-blue-800 mb-3">自我评估与定位</h4>
                            <ul class="space-y-2 text-blue-700 text-sm">
                                <li><strong>学术水平：</strong>GPA、年级排名、标化成绩</li>
                                <li><strong>专业兴趣：</strong>学科领域和职业方向</li>
                                <li><strong>个人偏好：</strong>地理位置、学校规模、校园文化</li>
                                <li><strong>财务预算：</strong>家庭可支持的费用范围</li>
                            </ul>
                        </div>
                        
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold text-green-800 mb-3">信息搜集渠道</h4>
                            <ul class="space-y-2 text-green-700 text-sm">
                                <li><strong>官方排名：</strong>U.S. News, QS, Times等</li>
                                <li><strong>学校官网：</strong>最准确、最全面的信息</li>
                                <li><strong>学生评价：</strong>Niche, Reddit等平台</li>
                                <li><strong>教育展：</strong>与招生官直接交流</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="bg-gray-50 p-6 rounded-lg mb-6">
                        <h4 class="font-bold text-gray-800 mb-3">"冲刺-匹配-保底"选校策略</h4>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="bg-red-50 p-4 rounded-lg">
                                <h5 class="font-bold text-red-800 mb-2">冲刺校 (2-3所)</h5>
                                <p class="text-sm text-red-700">录取要求高于现有水平的"梦想学校"</p>
                            </div>
                            <div class="bg-blue-50 p-4 rounded-lg">
                                <h5 class="font-bold text-blue-800 mb-2">匹配校 (4-6所)</h5>
                                <p class="text-sm text-blue-700">学术背景与录取水平相当的学校</p>
                            </div>
                            <div class="bg-green-50 p-4 rounded-lg">
                                <h5 class="font-bold text-green-800 mb-2">保底校 (2-3所)</h5>
                                <p class="text-sm text-green-700">条件明显高于录取标准的学校</p>
                            </div>
                        </div>
                    </div>
                `
            },
            {
                id: "section1-7",
                title: "7. 申请提交流程",
                icon: "fas fa-paper-plane",
                content: `
                    <p class="mb-6">完成所有材料的准备后，就进入了最后的申请提交阶段。熟悉主流的申请系统和提交流程，能确保你的申请被顺利、准时地送达。</p>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-6 rounded-lg">
                            <h4 class="font-bold text-blue-800 mb-3">主流申请系统</h4>
                            <ul class="space-y-2 text-blue-700 text-sm">
                                <li><strong>Common Application：</strong>美国最主流系统</li>
                                <li><strong>UCAS：</strong>英国大学唯一官方渠道</li>
                                <li><strong>Coalition for College：</strong>美国新兴平台</li>
                                <li><strong>ApplyTexas：</strong>德克萨斯州专用</li>
                            </ul>
                        </div>
                        
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold text-green-800 mb-3">提交步骤</h4>
                            <ol class="space-y-2 text-green-700 text-sm list-decimal list-inside">
                                <li>注册账户并选择学校</li>
                                <li>填写主申请表</li>
                                <li>完成各校补充材料</li>
                                <li>邀请推荐人并分配</li>
                                <li>上传和寄送材料</li>
                                <li>预览、支付并提交</li>
                            </ol>
                        </div>
                    </div>
                    
                    <div class="bg-red-50 border border-red-200 p-4 rounded-lg">
                        <h4 class="font-bold text-red-800 mb-2">重要提示：</h4>
                        <ul class="list-disc list-inside space-y-1 text-red-700 text-sm">
                            <li><strong>切勿拖延</strong>：不要等到截止日期最后一刻才提交</li>
                            <li><strong>注意时差</strong>：所有截止日期都是指当地时间</li>
                            <li><strong>保留副本</strong>：为所有材料保留备份</li>
                        </ul>
                    </div>
                `
            },
            {
                id: "section1-8",
                title: "8. 签证申请",
                icon: "fas fa-passport",
                content: `
                    <p class="mb-6">收到心仪大学的录取通知书并接受后，就进入了申请学生签证的关键步骤。签证是你能否合法进入并停留在目标国家学习的凭证。</p>
                    
                    <div class="bg-blue-50 p-6 rounded-lg mb-6">
                        <h4 class="font-bold text-blue-800 mb-3">签证申请的基本逻辑</h4>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="bg-white p-4 rounded-lg">
                                <h5 class="font-bold text-blue-900 mb-2">明确学习目的</h5>
                                <p class="text-sm text-blue-700">访问该国的唯一且真实目的就是全日制学习</p>
                            </div>
                            <div class="bg-white p-4 rounded-lg">
                                <h5 class="font-bold text-blue-900 mb-2">充足资金支持</h5>
                                <p class="text-sm text-blue-700">有足够经济能力支付学费和生活费</p>
                            </div>
                            <div class="bg-white p-4 rounded-lg">
                                <h5 class="font-bold text-blue-900 mb-2">无移民倾向</h5>
                                <p class="text-sm text-blue-700">完成学业后按时回国，与祖国有紧密联系</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold text-green-800 mb-3">核心文件</h4>
                            <ul class="space-y-2 text-green-700 text-sm">
                                <li><strong>美国：</strong>I-20 表格</li>
                                <li><strong>英国：</strong>CAS确认函</li>
                                <li><strong>澳大利亚：</strong>CoE注册确认书</li>
                                <li><strong>加拿大：</strong>LOA录取通知书</li>
                            </ul>
                        </div>
                        
                        <div class="bg-purple-50 p-6 rounded-lg">
                            <h4 class="font-bold text-purple-800 mb-3">通用材料</h4>
                            <ul class="space-y-2 text-purple-700 text-sm">
                                <li>有效护照</li>
                                <li>签证申请表</li>
                                <li>资金证明</li>
                                <li>学术材料</li>
                                <li>证件照</li>
                                <li>申请费收据</li>
                            </ul>
                        </div>
                    </div>
                `
            },
            {
                id: "section1-9",
                title: "9. 行前准备",
                icon: "fas fa-suitcase",
                content: `
                    <p class="mb-6">恭喜你！拿到签证，意味着你的留学申请之路已基本走完。但这只是另一段精彩旅程的开始。充分的行前准备，能帮助你更快地适应和融入新的学习和生活环境。</p>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-6 rounded-lg">
                            <h4 class="font-bold text-blue-800 mb-3">学术与文件准备</h4>
                            <ul class="space-y-2 text-blue-700 text-sm">
                                <li><strong>确认入学事宜：</strong>报到日期、新生周安排</li>
                                <li><strong>体检和疫苗：</strong>完成必要的体检和疫苗接种</li>
                                <li><strong>重要文件备份：</strong>扫描并云端储存所有文件</li>
                                <li><strong>证件照备用：</strong>准备符合尺寸的证件照</li>
                            </ul>
                        </div>
                        
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold text-green-800 mb-3">财务与通讯准备</h4>
                            <ul class="space-y-2 text-green-700 text-sm">
                                <li><strong>换汇与缴费：</strong>准备当地货币现金</li>
                                <li><strong>国际信用卡：</strong>办理双币支付信用卡</li>
                                <li><strong>手机通讯：</strong>开通国际漫游服务</li>
                                <li><strong>了解运营商：</strong>提前了解当地电信服务</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="bg-yellow-50 p-6 rounded-lg mb-6">
                        <h4 class="font-bold text-yellow-800 mb-3">行李准备清单</h4>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <h5 class="font-semibold mb-2">随身行李：</h5>
                                <ul class="text-sm text-yellow-700 space-y-1 list-disc list-inside">
                                    <li>所有重要文件</li>
                                    <li>现金和信用卡</li>
                                    <li>笔记本电脑和手机</li>
                                    <li>少量应急药品</li>
                                    <li>一件外套</li>
                                </ul>
                            </div>
                            <div>
                                <h5 class="font-semibold mb-2">托运行李：</h5>
                                <ul class="text-sm text-yellow-700 space-y-1 list-disc list-inside">
                                    <li>适合当地气候的衣物</li>
                                    <li>学习用品和专业书籍</li>
                                    <li>转换插头和插线板</li>
                                    <li>个人洗漱用品</li>
                                    <li>中国特色小礼物</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="bg-purple-50 border border-purple-200 p-4 rounded-lg">
                        <h4 class="font-bold text-purple-800 mb-2">心理与安全准备：</h4>
                        <ul class="list-disc list-inside space-y-1 text-purple-700 text-sm">
                            <li><strong>调整心态</strong>：了解和正视可能的文化冲击</li>
                            <li><strong>了解法规</strong>：初步了解当地法律法规和习俗</li>
                            <li><strong>安全意识</strong>：记住紧急联系电话和重要机构信息</li>
                        </ul>
                    </div>
                `
            }
        ]
    },
    part2: {
        title: "第二部分：各国特色指南",
        description: "了解热门留学目的地的特色和申请要求",
        countries: [
            {
                id: "section2-1",
                name: "美国",
                icon: "fas fa-flag-usa",
                color: "from-red-500 to-red-600",
                summary: "通识教育，整体评估，世界顶尖教育",
                content: `
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">教育体系特点</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>通识教育：</strong>前两年广泛学习不同学科，后两年确定专业方向</li>
                                <li><strong>院校类型多样：</strong>综合性大学、文理学院、社区大学</li>
                                <li><strong>学术灵活性：</strong>转学、转专业、双专业非常普遍</li>
                                <li><strong>整体评估：</strong>综合评估GPA、标化、文书、推荐信、课外活动等</li>
                            </ul>
                        </div>
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">申请要求</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>语言要求：</strong>托福100+/雅思7.0+</li>
                                <li><strong>标化考试：</strong>SAT 1500+/ACT 34+（可选但建议提交）</li>
                                <li><strong>申请系统：</strong>Common Application等通用申请平台</li>
                                <li><strong>费用：</strong>每年约$40,000-$110,000</li>
                            </ul>
                        </div>
                    </div>
                    <div class="bg-red-50 border border-red-200 p-4 rounded-lg">
                        <h4 class="font-bold text-red-800 mb-2">注意事项：</h4>
                        <ul class="list-disc list-inside space-y-1 text-red-700 text-sm">
                            <li>尽早规划课外活动，注重深度和持续性</li>
                            <li>精心打磨文书，讲述自己独特的故事</li>
                            <li>准备好面签，提前模拟练习面签问题</li>
                        </ul>
                    </div>
                `
            },
            {
                id: "section2-2",
                name: "英国",
                icon: "fas fa-crown",
                color: "from-blue-500 to-blue-600",
                summary: "专业导向，学制短，历史悠久",
                content: `
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">教育体系特点</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>专业导向：</strong>从大一开始直接进入专业课学习</li>
                                <li><strong>学制短：</strong>本科三年制（苏格兰四年制），硕士一年制</li>
                                <li><strong>教学模式：</strong>讲座、研讨课和辅导课相结合</li>
                                <li><strong>质量评估：</strong>严格的教育质量保证体系</li>
                            </ul>
                        </div>
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">申请要求</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>语言要求：</strong>雅思6.5-7.5，单项不低于6.0</li>
                                <li><strong>学术要求：</strong>A-Level达到A*AA-AAA或IB 38-42分</li>
                                <li><strong>申请系统：</strong>UCAS统一申请，最多选择5个课程</li>
                                <li><strong>费用：</strong>每年约£30,000-£58,000</li>
                            </ul>
                        </div>
                    </div>
                    <div class="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                        <h4 class="font-bold text-blue-800 mb-2">注意事项：</h4>
                        <ul class="list-disc list-inside space-y-1 text-blue-700 text-sm">
                            <li>尽早规划专业方向，英国本科直接进入专业学习</li>
                            <li>个人陈述是关键，突出对学科的热情和理解</li>
                            <li>关注UCAS截止日期，牛剑申请截止时间更早</li>
                        </ul>
                    </div>
                `
            },
            {
                id: "section2-3",
                name: "加拿大",
                icon: "fas fa-maple-leaf",
                color: "from-red-600 to-red-700",
                summary: "公立教育，性价比高，移民友好",
                content: `
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">教育体系特点</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>公立教育为主：</strong>教育质量均衡，标准高</li>
                                <li><strong>省份差异：</strong>各省有独立的教育管辖权</li>
                                <li><strong>实用主义导向：</strong>注重理论与实践结合</li>
                                <li><strong>Co-op项目：</strong>带薪实习项目丰富</li>
                            </ul>
                        </div>
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">申请要求</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>语言要求：</strong>雅思6.5或托福90分</li>
                                <li><strong>学术要求：</strong>高考成绩达到一本线以上</li>
                                <li><strong>申请系统：</strong>各省有不同的申请系统</li>
                                <li><strong>费用：</strong>每年约CAD $45,000-$75,000</li>
                            </ul>
                        </div>
                    </div>
                    <div class="bg-red-50 border border-red-200 p-4 rounded-lg">
                        <h4 class="font-bold text-red-800 mb-2">注意事项：</h4>
                        <ul class="list-disc list-inside space-y-1 text-red-700 text-sm">
                            <li>提前了解各省申请系统，熟悉相应平台和截止日期</li>
                            <li>重视Co-op机会，对就业和移民有很大帮助</li>
                            <li>充分准备资金证明，要求较为严格</li>
                        </ul>
                    </div>
                `
            },
            {
                id: "section2-4",
                name: "澳大利亚",
                icon: "fas fa-sun",
                color: "from-green-500 to-green-600",
                summary: "八大名校，接受高考，环境优美",
                content: `
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">教育体系特点</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>八大名校联盟：</strong>澳洲顶尖研究型大学联盟</li>
                                <li><strong>注重职业技能：</strong>TAFE系统提供职业教育</li>
                                <li><strong>灵活学年制：</strong>2月和7月两次入学机会</li>
                                <li><strong>接受高考：</strong>除墨尔本大学外都接受高考成绩</li>
                            </ul>
                        </div>
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">申请要求</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>语言要求：</strong>雅思6.5或托福79-90分</li>
                                <li><strong>学术要求：</strong>高考达到各省一本线或更高</li>
                                <li><strong>申请方式：</strong>直接向大学申请或通过中介</li>
                                <li><strong>费用：</strong>每年约AUD $60,000-$90,000</li>
                            </ul>
                        </div>
                    </div>
                    <div class="bg-green-50 border border-green-200 p-4 rounded-lg">
                        <h4 class="font-bold text-green-800 mb-2">注意事项：</h4>
                        <ul class="list-disc list-inside space-y-1 text-green-700 text-sm">
                            <li>利用好高考成绩，澳洲是直接进入世界名校的好选择</li>
                            <li>认真准备GS材料，证明真实的学习意图</li>
                            <li>考虑地区加分，偏远地区学习对移民有帮助</li>
                        </ul>
                    </div>
                `
            },
            {
                id: "section2-5",
                name: "德国",
                icon: "fas fa-cog",
                color: "from-gray-700 to-gray-800",
                summary: "工程强国，免学费，严谨治学",
                content: `
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">教育体系特点</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>公立大学免学费：</strong>只需缴纳少量注册费</li>
                                <li><strong>双元制教育：</strong>理论与实践高度结合</li>
                                <li><strong>严谨学术传统：</strong>在工程、科学等领域世界领先</li>
                                <li><strong>应用科学大学：</strong>偏向实践和就业</li>
                            </ul>
                        </div>
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">申请要求</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>APS审核：</strong>必须通过学历审核</li>
                                <li><strong>语言要求：</strong>德语TestDaF 4*4或英语雅思6.5+</li>
                                <li><strong>学术要求：</strong>需在国内大学读满相应学期</li>
                                <li><strong>费用：</strong>每年约€11,000-€13,000</li>
                            </ul>
                        </div>
                    </div>
                    <div class="bg-gray-50 border border-gray-200 p-4 rounded-lg">
                        <h4 class="font-bold text-gray-800 mb-2">注意事项：</h4>
                        <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                            <li>尽早准备APS审核，是申请德国大学的第一道门槛</li>
                            <li>学好德语是王道，即使选择英语授课也要学德语</li>
                            <li>课程匹配度很重要，转专业申请难度较大</li>
                        </ul>
                    </div>
                `
            },
            {
                id: "section2-6",
                name: "法国",
                icon: "fas fa-wine-glass",
                color: "from-blue-600 to-blue-700",
                summary: "精英教育，文化底蕴，费用低廉",
                content: `
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">教育体系特点</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>双轨制教育：</strong>综合性大学和精英学校</li>
                                <li><strong>LMD三级学位制：</strong>学士-硕士-博士体系</li>
                                <li><strong>深厚文化底蕴：</strong>世界一流的文化艺术教育</li>
                                <li><strong>精英学校：</strong>严苛选拔，高质量培养</li>
                            </ul>
                        </div>
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">申请要求</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>Campus France评估：</strong>必须通过官方评估</li>
                                <li><strong>语言要求：</strong>法语TCF B2/C1或英语雅思6.5+</li>
                                <li><strong>学术要求：</strong>重视教育背景匹配度</li>
                                <li><strong>费用：</strong>每年约€11,000-€18,000</li>
                            </ul>
                        </div>
                    </div>
                    <div class="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                        <h4 class="font-bold text-blue-800 mb-2">注意事项：</h4>
                        <ul class="list-disc list-inside space-y-1 text-blue-700 text-sm">
                            <li>法语学习是重中之重，是成功留学法国的基石</li>
                            <li>认真准备Campus France面试，清晰阐述留学计划</li>
                            <li>了解不同院校类型，根据目标选择合适的院校</li>
                        </ul>
                    </div>
                `
            },
            {
                id: "section2-7",
                name: "新加坡",
                icon: "fas fa-city",
                color: "from-red-500 to-red-600",
                summary: "亚洲枢纽，双语环境，精英教育",
                content: `
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">教育体系特点</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>精英教育：</strong>NUS、NTU常年位居世界前列</li>
                                <li><strong>双语环境：</strong>英语授课，华语通用</li>
                                <li><strong>与业界紧密结合：</strong>提供大量实习和交流机会</li>
                                <li><strong>亚洲十字路口：</strong>东西方文化交融</li>
                            </ul>
                        </div>
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">申请要求</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>语言要求：</strong>雅思6.5-7.0或托福92-100+</li>
                                <li><strong>学术要求：</strong>高考超一本线或A-Level/IB优异成绩</li>
                                <li><strong>申请方式：</strong>直接向大学申请</li>
                                <li><strong>费用：</strong>每年约SGD $33,000-$45,000（含助学金）</li>
                            </ul>
                        </div>
                    </div>
                    <div class="bg-red-50 border border-red-200 p-4 rounded-lg">
                        <h4 class="font-bold text-red-800 mb-2">注意事项：</h4>
                        <ul class="list-disc list-inside space-y-1 text-red-700 text-sm">
                            <li>竞争异常激烈，务必在学术和综合背景上都做到顶尖</li>
                            <li>慎重考虑助学金协议，意味着三年工作合约</li>
                            <li>利用地理优势，拓展国际视野</li>
                        </ul>
                    </div>
                `
            },
            {
                id: "section2-8",
                name: "日本",
                icon: "fas fa-torii-gate",
                color: "from-pink-500 to-pink-600",
                summary: "科研强国，文化独特，奖学金丰富",
                content: `
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">教育体系特点</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>研究型导向：</strong>帝国大学拥有世界一流科研设施</li>
                                <li><strong>国公立与私立并存：</strong>各具特色</li>
                                <li><strong>严谨学术氛围：</strong>匠人精神贯穿教育</li>
                                <li><strong>奖学金丰富：</strong>MEXT奖学金和学费减免政策</li>
                            </ul>
                        </div>
                        <div class="bg-green-50 p-6 rounded-lg">
                            <h4 class="font-bold mb-3">申请要求</h4>
                            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
                                <li><strong>EJU考试：</strong>日本留学试验是申请核心</li>
                                <li><strong>语言要求：</strong>日语N1/N2或托福80+（SGU项目）</li>
                                <li><strong>校内考：</strong>各大学独立考试和面试</li>
                                <li><strong>费用：</strong>每年约120-250万日元</li>
                            </ul>
                        </div>
                    </div>
                    <div class="bg-pink-50 border border-pink-200 p-4 rounded-lg">
                        <h4 class="font-bold text-pink-800 mb-2">注意事项：</h4>
                        <ul class="list-disc list-inside space-y-1 text-pink-700 text-sm">
                            <li>提前规划EJU备考，至少提前一年开始系统备考</li>
                            <li>日语和英语并重，优秀双语能力更具优势</li>
                            <li>积极关注奖学金信息，主动申请</li>
                        </ul>
                    </div>
                `
            }
        ]
    }
};

// 导出数据供其他文件使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = guideContent;
}
