/**
 * famousCases.js — 紫微斗数经典名人命例库
 *
 * 收录历史/近代知名人物公开生辰，用于研究学习。
 * 数据来源：紫微斗数论坛/古籍/公开传记
 *
 * ⚠ 仅供研究学习用途，不作实际占断使用
 */

export const FAMOUS_CASES = [
  {
    id: 'principal_yyx',
    name: '主用例 · 1990 庚午年',
    desc: '紫贪同宫格 · 卯位坎命',
    category: '主用例',
    year: 1990, month: 5, day: 22, hour: 5,
    gender: '男',
    is_lunar: true,
    longitude: 104.06,  // 成都
    highlights: ['紫微+贪狼坐命卯宫', '紫贪同宫格', '杀破狼三方会照'],
  },
  {
    id: 'mao_zedong',
    name: '毛泽东',
    desc: '1893-12-26 凌晨子时（湖南韶山）',
    category: '近代政治家',
    year: 1893, month: 11, day: 19, hour: 23,
    gender: '男',
    is_lunar: true,
    longitude: null,  // 1949 前无北京时区
    highlights: ['天府坐命子位', '紫府朝垣格', '帝王之相'],
  },
  {
    id: 'zhou_enlai',
    name: '周恩来',
    desc: '1898-03-05 卯时（江苏淮安）',
    category: '近代政治家',
    year: 1898, month: 2, day: 13, hour: 5,
    gender: '男',
    is_lunar: true,
    longitude: null,  // 1949 前无北京时区
    highlights: ['七杀朝斗格', '辅佐之命'],
  },
  {
    id: 'wang_yongqing',
    name: '王永庆（台塑创办人）',
    desc: '1917-01-18 戌时（台北新店）',
    category: '商业巨子',
    year: 1916, month: 12, day: 24, hour: 19,
    gender: '男',
    is_lunar: true,
    longitude: null,  // 1949 前无北京时区
    highlights: ['武曲化禄入财帛', '财官双美格'],
  },
  {
    id: 'li_jiacheng',
    name: '李嘉诚',
    desc: '1928-07-29 午时（广东潮州）',
    category: '商业巨子',
    year: 1928, month: 6, day: 13, hour: 11,
    gender: '男',
    is_lunar: true,
    longitude: null,  // 1949 前无北京时区
    highlights: ['天相坐命', '武曲化禄', '财库丰厚'],
  },
  {
    id: 'einstein',
    name: '爱因斯坦',
    desc: '1879-03-14 上午（德国乌尔姆当地时间）',
    category: '历史名人',
    year: 1879, month: 2, day: 22, hour: 9,
    gender: '男',
    is_lunar: true,
    longitude: null,  // 不校正（已用当地时间）
    highlights: ['天机坐命', '文星拱命', '科学之星'],
  },
  {
    id: 'jin_yong',
    name: '金庸（查良镛）',
    desc: '1924-03-10 午时（浙江海宁）',
    category: '文化名人',
    year: 1924, month: 2, day: 6, hour: 11,
    gender: '男',
    is_lunar: true,
    longitude: null,  // 1949 前无北京时区
    highlights: ['文昌文曲朝命', '文笔之星'],
  },
  {
    id: 'cixi',
    name: '慈禧太后',
    desc: '1835-11-29 卯时（北京）',
    category: '历史帝王',
    year: 1835, month: 10, day: 10, hour: 5,
    gender: '女',
    is_lunar: true,
    longitude: null,  // 1949 前无北京时区
    highlights: ['女主掌权', '紫微化权'],
  },
]

// 按分类分组
export function groupCasesByCategory() {
  const groups = {}
  for (const c of FAMOUS_CASES) {
    if (!groups[c.category]) groups[c.category] = []
    groups[c.category].push(c)
  }
  return groups
}
