'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  ArrowLeft, BarChart3, Bell, BookOpen, Check, ChevronRight, CircleAlert,
  ClipboardCheck, Clock3, Heart, House, Leaf, MapPin, PackageCheck, Plus,
  Search, ShieldCheck, ShoppingBag, Soup, Store, TreePine, TrendingUp,
  UserRound, UsersRound, X,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';

type Role = 'student' | 'merchant' | 'admin';
type StudentView = 'home' | 'orders' | 'community' | 'profile';
type MerchantView = 'shop' | 'products' | 'pickup';
type AdminView = 'dashboard' | 'audit' | 'users' | 'risk';

type Product = {
  id: number; name: string; shop: string; category: string; taste: '清淡' | '麻辣' | '甜口';
  price: number; original: number; distance: number; pickup: string; left: number;
  image: string; allergens: string[]; views: number; likedBy: number;
};

const products: Product[] = [
  { id: 1, name: '暖食便当惊喜盒', shop: '南苑食堂 · 暖食档', category: '简餐', taste: '清淡', price: 9.9, original: 28, distance: 0.3, pickup: '18:30–20:00', left: 3, image: '/food-bento.jpg', allergens: [], views: 126, likedBy: 18 },
  { id: 2, name: '面包房晚安袋', shop: '学生活动中心 · 麦香屋', category: '烘焙', taste: '甜口', price: 12, original: 36, distance: 0.7, pickup: '19:00–21:00', left: 5, image: '/food-bread.jpg', allergens: ['花生'], views: 98, likedBy: 26 },
  { id: 3, name: '轻食能量盲盒', shop: '图书馆北门 · 绿芽', category: '轻食', taste: '清淡', price: 11.8, original: 32, distance: 0.9, pickup: '17:45–19:15', left: 2, image: '/food-salad.jpg', allergens: [], views: 87, likedBy: 14 },
  { id: 4, name: '鲜果缤纷盒', shop: '西门生活馆 · 鲜果时光', category: '水果', taste: '甜口', price: 8.8, original: 22, distance: 1.1, pickup: '20:00–21:30', left: 4, image: '/food-fruit.jpg', allergens: [], views: 73, likedBy: 11 },
  { id: 5, name: '川味小炒双拼', shop: '东苑二楼 · 川香小馆', category: '简餐', taste: '麻辣', price: 10, original: 25, distance: 0.8, pickup: '18:00–19:30', left: 6, image: '/food-spicy.jpg', allergens: [], views: 154, likedBy: 32 },
  { id: 6, name: '奶茶与小点心', shop: '教学楼 B 座 · 小满茶铺', category: '饮品', taste: '甜口', price: 7.9, original: 21, distance: 0.4, pickup: '19:30–21:00', left: 3, image: '/food-drink.jpg', allergens: [], views: 108, likedBy: 20 },
];

const communityItems = [
  { id: 1, kind: '勤工助学', title: '周末活动签到协助', org: '校友中心', reward: '¥25/时', time: '周六 13:30', note: '需要 2 位同学，负责签到与现场引导。' },
  { id: 2, kind: '校园互助', title: '帮忙取图书馆预约书', org: '林同学', reward: '¥8', time: '今晚 19:00 前', note: '取完放到 3 号宿舍楼前台即可。' },
  { id: 3, kind: '勤工助学', title: '咖啡店晚班小助手', org: '小岛咖啡', reward: '¥28/时', time: '每周二、四', note: '18:00–21:00，可提供简单培训。' },
];

const pendingMerchants = [
  { id: 1, shop: '桃桃面包铺', owner: '周女士', location: '学校东门 120 米', submitted: '今天 10:24' },
  { id: 2, shop: '一碗小食堂', owner: '陈先生', location: '南苑生活区', submitted: '昨天 18:46' },
];

const riskSeed = [
  { id: 1, type: '价格异常', item: '豪华午餐盲盒', shop: '香满园', detail: '折扣价 ¥35 高于原价 ¥28', level: '已拦截' },
  { id: 2, type: '有效期过短', item: '奶油蛋糕切块', shop: '甜野烘焙', detail: '距离失效仅 38 分钟', level: '待复核' },
  { id: 3, type: '内容风险', item: '兼职信息', shop: '普通用户', detail: '包含站外联系方式', level: '已拦截' },
];

const categoryFilters = ['全部', '简餐', '烘焙', '轻食', '水果', '饮品'];

function Logo({ compact = false }: { compact?: boolean }) {
  return <div className="flex items-center gap-2.5"><span className="logo-stamp relative grid size-11 place-items-center rounded-[17px] bg-primary text-primary-foreground"><Soup className="size-6" /><Leaf className="absolute -right-1 -top-1 size-4 rotate-12 rounded-full bg-[#8fb979] p-0.5 text-white" /></span>{!compact && <span className="font-heading text-2xl font-black tracking-tight">食愿</span>}</div>;
}

function DoodleTitle({ eyebrow, title, note }: { eyebrow?: string; title: string; note?: string }) {
  return <div>{eyebrow && <p className="mb-1 text-sm font-bold text-primary">{eyebrow}</p>}<h1 className="font-heading text-3xl font-black tracking-[-.035em] sm:text-4xl">{title}</h1>{note && <p className="mt-2 text-base leading-7 text-muted-foreground">{note}</p>}</div>;
}

function MiniStat({ label, value, tint = 'peach' }: { label: string; value: string; tint?: 'peach' | 'green' | 'yellow' }) {
  const tints = { peach: 'bg-[#ffe2d3]', green: 'bg-[#e2efd7]', yellow: 'bg-[#fff0bd]' };
  return <div className={`rounded-[22px] ${tints[tint]} p-5`}><p className="text-sm font-medium text-[#766357]">{label}</p><p className="mt-2 font-heading text-3xl font-black text-[#493a30]">{value}</p></div>;
}

export default function Home() {
  const [role, setRole] = useState<Role>('student');
  const [studentView, setStudentView] = useState<StudentView>('home');
  const [merchantView, setMerchantView] = useState<MerchantView>('shop');
  const [adminView, setAdminView] = useState<AdminView>('dashboard');
  const [filter, setFilter] = useState('全部');
  const [query, setQuery] = useState('');
  const [taste, setTaste] = useState<'清淡' | '麻辣'>('清淡');
  const [taboos, setTaboos] = useState(['花生', '海鲜']);
  const [favorites, setFavorites] = useState<number[]>([3]);
  const [selected, setSelected] = useState<Product | null>(null);
  const [orderDone, setOrderDone] = useState(false);
  const [orders, setOrders] = useState([{ id: 101, productId: 3, code: '371 482', status: '待领取', created: '今天 17:26' }]);
  const [loginOpen, setLoginOpen] = useState(false);
  const [loginRole, setLoginRole] = useState<Role>('student');
  const [authMode, setAuthMode] = useState<'login' | 'register' | 'reset'>('login');
  const [publishOpen, setPublishOpen] = useState(false);
  const [publishError, setPublishError] = useState('');
  const [publishSuccess, setPublishSuccess] = useState(false);
  const [originalPrice, setOriginalPrice] = useState('28');
  const [discountPrice, setDiscountPrice] = useState('9.9');
  const [pickupOpen, setPickupOpen] = useState(false);
  const [pickupCode, setPickupCode] = useState('');
  const [pickupMessage, setPickupMessage] = useState('');
  const [approved, setApproved] = useState<number[]>([]);
  const [disabledUsers, setDisabledUsers] = useState<number[]>([3]);
  const [riskLogs, setRiskLogs] = useState(riskSeed);
  const [notice, setNotice] = useState('');

  const recommended = useMemo(() => products
    .filter((p) => (filter === '全部' || p.category === filter) && !p.allergens.some((item) => taboos.includes(item)) && (!query || `${p.name}${p.shop}${p.category}`.includes(query)))
    .sort((a, b) => Number(b.taste === taste) - Number(a.taste === taste) || a.distance - b.distance), [filter, query, taste, taboos]);

  const guessed = products.filter((p) => p.likedBy >= 20 && !p.allergens.some((item) => taboos.includes(item))).slice(0, 3);

  function flash(message: string) {
    setNotice(message);
    window.setTimeout(() => setNotice(''), 2600);
  }

  function switchRole(next: Role) {
    setRole(next);
    setStudentView('home'); setMerchantView('shop'); setAdminView('dashboard');
    setLoginOpen(false); setAuthMode('login'); window.scrollTo({ top: 0, behavior: 'smooth' });
    flash(next === 'student' ? '已进入学生端' : next === 'merchant' ? '已进入商家端' : '已进入管理员端');
  }

  function placeOrder(product: Product) {
    const code = String(Math.floor(100000 + Math.random() * 900000));
    setOrders((current) => [{ id: Date.now(), productId: product.id, code: `${code.slice(0, 3)} ${code.slice(3)}`, status: '待领取', created: '刚刚' }, ...current]);
    setOrderDone(true);
  }

  function publishProduct() {
    const original = Number(originalPrice); const discount = Number(discountPrice);
    if (!original || !discount) { setPublishError('请填写完整的价格信息'); return; }
    if (discount > original) { setPublishError('折扣价不能高于原价，这条发布已被安全检查拦下。'); return; }
    if (discount / original < 0.1) { setPublishError('折扣低于一折，请确认商品情况后再发布。'); return; }
    setPublishError(''); setPublishSuccess(true);
  }

  function verifyPickup() {
    if (pickupCode.replace(/\s/g, '') === '482619') { setPickupMessage('核销成功，祝同学用餐愉快！'); flash('订单已完成'); }
    else setPickupMessage('取餐码不正确，请和同学确认后重试。');
  }

  useEffect(() => {
    const context = (document as Document & { modelContext?: { registerTool: (tool: unknown, options?: { signal?: AbortSignal }) => void | Promise<void> } }).modelContext;
    if (!context?.registerTool) return;
    const lifecycle = new AbortController();
    void Promise.resolve(context.registerTool({
      name: 'reserve_food_box', title: '领取食物盲盒',
      description: '为当前学生领取指定编号的在售食物盲盒，并在页面中生成取餐订单。',
      inputSchema: { type: 'object', properties: { productId: { type: 'number' } }, required: ['productId'], additionalProperties: false },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute(input: unknown) {
        const productId = Number((input as { productId?: number })?.productId);
        const product = products.find((item) => item.id === productId);
        if (!product) throw new Error('没有找到这个在售盲盒');
        placeOrder(product); setSelected(product);
        return { status: 'reserved', productId, productName: product.name };
      },
    }, { signal: lifecycle.signal })).catch(() => undefined);
    return () => lifecycle.abort();
  }, []);

  const studentNav: { key: StudentView; label: string }[] = [{ key: 'home', label: '发现' }, { key: 'orders', label: '我的订单' }, { key: 'community', label: '愿望树' }, { key: 'profile', label: '我的' }];
  const merchantNav: { key: MerchantView; label: string }[] = [{ key: 'shop', label: '店铺概览' }, { key: 'products', label: '商品管理' }, { key: 'pickup', label: '订单核销' }];
  const adminNav: { key: AdminView; label: string }[] = [{ key: 'dashboard', label: '数据概览' }, { key: 'audit', label: '商家审核' }, { key: 'users', label: '用户管理' }, { key: 'risk', label: '安全日志' }];

  return <main className="min-h-screen pb-20 text-foreground md:pb-0">
    {notice && <div className="fixed left-1/2 top-5 z-[90] flex -translate-x-1/2 items-center gap-2 rounded-full bg-[#5f7f57] px-5 py-3 text-sm font-bold text-white shadow-xl"><Check className="size-4" />{notice}</div>}

    <header className="sticky top-0 z-40 border-b border-border/75 bg-[#fff9ed]/94 backdrop-blur-xl">
      <div className="mx-auto flex h-[76px] max-w-7xl items-center gap-5 px-5 sm:px-8">
        <button onClick={() => role === 'student' ? setStudentView('home') : role === 'merchant' ? setMerchantView('shop') : setAdminView('dashboard')} aria-label="回到首页"><Logo /></button>
        <nav className="ml-6 hidden items-center gap-1 rounded-full bg-secondary p-1 md:flex" aria-label="主要导航">
          {role === 'student' && studentNav.map((item) => <button key={item.key} onClick={() => setStudentView(item.key)} className={`nav-pill ${studentView === item.key ? 'nav-pill-active' : ''}`}>{item.label}</button>)}
          {role === 'merchant' && merchantNav.map((item) => <button key={item.key} onClick={() => setMerchantView(item.key)} className={`nav-pill ${merchantView === item.key ? 'nav-pill-active' : ''}`}>{item.label}</button>)}
          {role === 'admin' && adminNav.map((item) => <button key={item.key} onClick={() => setAdminView(item.key)} className={`nav-pill ${adminView === item.key ? 'nav-pill-active' : ''}`}>{item.label}</button>)}
        </nav>
        {role === 'student' && studentView === 'home' && <div className="ml-auto hidden w-full max-w-[270px] items-center gap-2 rounded-full border border-border bg-card px-4 py-2.5 sm:flex"><Search className="size-4 text-muted-foreground" /><input value={query} onChange={(e) => setQuery(e.target.value)} className="w-full bg-transparent text-sm outline-none" placeholder="找找今晚想吃的" aria-label="搜索食物" />{query && <button onClick={() => setQuery('')}><X className="size-4 text-muted-foreground" /></button>}</div>}
        <div className={`${role === 'student' && studentView === 'home' ? '' : 'ml-auto'} flex items-center gap-2`}>
          {role === 'merchant' && <Button onClick={() => { setPublishOpen(true); setPublishSuccess(false); }} className="hidden rounded-full sm:flex"><Plus className="size-4" />发布商品</Button>}
          <button className="hidden size-10 place-items-center rounded-full border border-border bg-card text-muted-foreground sm:grid" aria-label="消息"><Bell className="size-4.5" /></button>
          <button onClick={() => { setLoginRole(role); setLoginOpen(true); setAuthMode('login'); }} className="flex items-center gap-2 rounded-full border border-border bg-card py-1.5 pl-1.5 pr-3 text-sm font-bold shadow-[0_3px_0_rgba(118,84,53,.06)]"><span className="grid size-8 place-items-center rounded-full bg-[#ffe1ce] text-primary"><UserRound className="size-4" /></span><span className="hidden sm:inline">{role === 'student' ? '林同学' : role === 'merchant' ? '暖食档' : '管理员'}</span><span className="text-xs text-muted-foreground">⌄</span></button>
        </div>
      </div>
    </header>

    {role === 'student' && studentView === 'home' && <>
      <section className="mx-auto max-w-7xl px-5 pt-7 sm:px-8 sm:pt-9">
        <div className="paper-card relative overflow-hidden rounded-[32px] border border-[#efd9bd] bg-[#fff1d5] p-7 sm:p-9">
          <span className="absolute -right-7 -top-10 text-[110px] opacity-20" aria-hidden>🍊</span><span className="absolute bottom-0 right-36 hidden text-7xl opacity-25 sm:block" aria-hidden>🌿</span>
          <div className="relative z-10 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <div><p className="mb-3 flex items-center gap-2 text-sm font-bold text-[#8b6c54]"><span className="text-xl">🍚</span> 晚上好，林同学</p><h1 className="font-heading text-3xl font-black leading-tight tracking-[-.03em] sm:text-4xl">附近有 <span className="soft-squiggle text-[#d96443]">14 份好味道</span><br className="hidden sm:block" /> 正等你带回去</h1><p className="mt-4 text-base text-muted-foreground">按你的清淡口味和预算排好了，海鲜与花生已避开。</p></div>
            <div className="flex items-center gap-4 rounded-[22px] bg-white/65 px-5 py-4"><span className="text-3xl">🌱</span><div><p className="text-sm text-muted-foreground">本月一起挽救</p><p className="font-heading text-2xl font-black">12.8 kg</p></div></div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-16 pt-9 sm:px-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between"><DoodleTitle eyebrow="为你优选" title="今晚吃点好的" note="近、合口味，也不会超出你的日常预算" /><div className="flex gap-2 overflow-x-auto pb-1">{categoryFilters.map((item) => <button key={item} onClick={() => setFilter(item)} className={`filter-chip ${filter === item ? 'filter-chip-active' : ''}`}>{item}</button>)}</div></div>
        {recommended.length ? <div className="mt-7 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{recommended.slice(0, 4).map((product, index) => <ProductCard key={product.id} product={product} rank={index} favorite={favorites.includes(product.id)} onFavorite={() => setFavorites((current) => current.includes(product.id) ? current.filter((id) => id !== product.id) : [...current, product.id])} onOpen={() => { setSelected(product); setOrderDone(false); }} />)}</div> : <div className="paper-card mt-7 rounded-[28px] border border-dashed border-border bg-card p-12 text-center"><span className="text-4xl">🥣</span><h3 className="mt-3 font-heading text-xl font-black">这一类暂时卖完啦</h3><p className="mt-2 text-muted-foreground">换个分类看看，新的盲盒也会很快上架。</p><Button onClick={() => setFilter('全部')} variant="outline" className="mt-5 rounded-full">看看全部</Button></div>}

        <div className="mt-12 flex items-end justify-between"><DoodleTitle eyebrow="猜你喜欢" title="同口味的同学也在选" note="来自相似饮食偏好的真实收藏与下单" /><span className="hidden rounded-full bg-[#e4efd8] px-4 py-2 text-sm font-bold text-[#58764f] sm:inline">已过滤你的忌口 ✓</span></div>
        <div className="mt-6 grid gap-4 md:grid-cols-3">{guessed.map((product) => <button key={product.id} onClick={() => { setSelected(product); setOrderDone(false); }} className="paper-card flex items-center gap-4 rounded-[24px] border border-border bg-card p-3.5 text-left transition hover:-translate-y-0.5"><img src={product.image} alt="" className="size-24 rounded-[18px] object-cover" /><div className="min-w-0"><p className="truncate font-heading text-lg font-black">{product.name}</p><p className="mt-1 text-sm text-muted-foreground">{product.likedBy} 位同口味同学喜欢</p><p className="mt-3 font-heading text-xl font-black text-primary">¥ {product.price.toFixed(1)}</p></div></button>)}</div>
      </section>
    </>}

    {role === 'student' && studentView === 'orders' && <StudentOrders orders={orders} onView={(product) => { setSelected(product); setOrderDone(true); }} />}

    {role === 'student' && studentView === 'community' && <section className="mx-auto max-w-6xl px-5 py-10 sm:px-8"><div className="relative overflow-hidden rounded-[30px] bg-[#e3efd9] p-8 sm:p-10"><span className="absolute -right-5 -top-8 text-8xl opacity-25">🌳</span><DoodleTitle eyebrow="校园愿望树" title="让一个小愿望，遇见顺路的你" note="勤工助学、跑腿互助和拼餐信息都在这里，不公开敏感身份标签。" /><Button onClick={() => flash('愿望发布入口已打开')} className="mt-6 rounded-full"><Plus className="size-4" />种下愿望</Button></div><div className="mt-8 grid gap-5 md:grid-cols-3">{communityItems.map((item) => <article key={item.id} className="paper-card rounded-[26px] border border-border bg-card p-6"><Badge className="rounded-full border-0 bg-[#fff0be] text-[#866324] hover:bg-[#fff0be]">{item.kind}</Badge><h2 className="mt-4 font-heading text-xl font-black">{item.title}</h2><p className="mt-2 leading-6 text-muted-foreground">{item.note}</p><div className="mt-5 flex items-center justify-between border-t border-border pt-4"><div><p className="font-bold">{item.org} · <span className="text-primary">{item.reward}</span></p><p className="mt-1 text-sm text-muted-foreground">{item.time}</p></div><Button onClick={() => flash('已回应，对方会在消息中心联系你')} variant="outline" className="rounded-full">我来帮忙</Button></div></article>)}</div></section>}

    {role === 'student' && studentView === 'profile' && <StudentProfile taste={taste} setTaste={setTaste} taboos={taboos} setTaboos={setTaboos} onSave={() => { setStudentView('home'); flash('偏好已保存，首页推荐已更新'); }} />}

    {role === 'merchant' && merchantView === 'shop' && <MerchantDashboard onPublish={() => { setPublishOpen(true); setPublishSuccess(false); }} onPrice={() => flash('建议价已采用，附近学生会看到更新')} />}
    {role === 'merchant' && merchantView === 'products' && <MerchantProducts onPublish={() => { setPublishOpen(true); setPublishSuccess(false); }} />}
    {role === 'merchant' && merchantView === 'pickup' && <MerchantPickup onOpen={() => { setPickupOpen(true); setPickupCode(''); setPickupMessage(''); }} />}

    {role === 'admin' && adminView === 'dashboard' && <AdminDashboard />}
    {role === 'admin' && adminView === 'audit' && <AdminAudit approved={approved} onAudit={(id, pass) => { setApproved((current) => [...current, id]); flash(pass ? '商家已通过审核，可正常登录发布商品' : '已驳回并通知商家补充资料'); }} />}
    {role === 'admin' && adminView === 'users' && <AdminUsers disabled={disabledUsers} onToggle={(id) => { setDisabledUsers((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]); flash(disabledUsers.includes(id) ? '账号已恢复使用' : '账号已暂时停用'); }} />}
    {role === 'admin' && adminView === 'risk' && <RiskLogs logs={riskLogs} onResolve={(id) => { setRiskLogs((current) => current.map((log) => log.id === id ? { ...log, level: '已处理' } : log)); flash('这条风险记录已处理'); }} />}

    <MobileNav role={role} studentView={studentView} merchantView={merchantView} adminView={adminView} onStudent={setStudentView} onMerchant={setMerchantView} onAdmin={setAdminView} />

    <Dialog open={!!selected} onOpenChange={(open) => !open && setSelected(null)}><DialogContent className="max-h-[92vh] overflow-y-auto rounded-[30px] p-0 sm:max-w-lg">{selected && !orderDone ? <><div className="relative aspect-[16/8] overflow-hidden rounded-t-[30px]"><img src={selected.image} alt={selected.name} className="h-full w-full object-cover" /><button onClick={() => setFavorites((current) => current.includes(selected.id) ? current.filter((id) => id !== selected.id) : [...current, selected.id])} className="absolute right-4 top-4 grid size-10 place-items-center rounded-full bg-white/90 text-primary"><Heart className={`size-5 ${favorites.includes(selected.id) ? 'fill-current' : ''}`} /></button></div><div className="px-6"><DialogHeader><p className="text-sm text-muted-foreground">{selected.shop}</p><DialogTitle className="font-heading text-2xl font-black">{selected.name}</DialogTitle><DialogDescription className="text-base leading-7">当天新鲜未售完的餐品，具体搭配以现场领取为准。商家已标注制作时间与领取期限。</DialogDescription></DialogHeader><div className="mt-5 rounded-[20px] bg-[#f1f6e8] p-4"><p className="font-bold text-[#55734f]">适合你的理由</p><p className="mt-1 text-sm leading-6 text-muted-foreground">{selected.taste}口味 · 价格在日常预算内 · 距离仅 {selected.distance} km</p></div><div className="mt-5 grid grid-cols-2 gap-3"><div className="rounded-[18px] border border-border p-4"><p className="text-sm text-muted-foreground">领取时间</p><p className="mt-1 font-bold">{selected.pickup}</p></div><div className="rounded-[18px] border border-border p-4"><p className="text-sm text-muted-foreground">取货距离</p><p className="mt-1 font-bold">{selected.distance} km</p></div></div><div className="mt-6 flex items-end justify-between"><div><p className="text-sm text-muted-foreground">盲盒价</p><p className="font-heading text-3xl font-black text-primary">¥ {selected.price.toFixed(1)} <span className="text-base font-medium text-muted-foreground line-through">¥ {selected.original}</span></p></div><p className="text-sm font-bold text-[#7b695c]">还剩 {selected.left} 份</p></div></div><DialogFooter className="mx-0 mb-0 mt-5 rounded-b-[30px] px-6"><Button onClick={() => placeOrder(selected)} className="w-full rounded-full py-5">确认领取</Button></DialogFooter></> : selected && <div className="p-7 text-center"><span className="mx-auto grid size-16 place-items-center rounded-full bg-[#e2efd7] text-[#587650]"><Check className="size-8" /></span><DialogTitle className="mt-5 font-heading text-2xl font-black">领取成功</DialogTitle><DialogDescription className="mt-2 text-base">在 {selected.pickup} 到店出示下面的取餐码。</DialogDescription><div className="mt-6 rounded-[24px] border-2 border-dashed border-[#efc498] bg-[#fff4de] p-6"><p className="text-sm font-bold text-muted-foreground">取餐码</p><p className="mt-2 font-heading text-4xl font-black tracking-[.16em]">{orders[0]?.code ?? '482 619'}</p><p className="mt-2 text-sm text-muted-foreground">{selected.shop}</p></div><Button onClick={() => { setSelected(null); setStudentView('orders'); }} className="mt-6 w-full rounded-full">查看我的订单</Button></div>}</DialogContent></Dialog>

    <AuthDialog open={loginOpen} setOpen={setLoginOpen} role={loginRole} setRole={setLoginRole} mode={authMode} setMode={setAuthMode} onLogin={switchRole} onNotice={flash} />
    <PublishDialog open={publishOpen} setOpen={setPublishOpen} success={publishSuccess} error={publishError} original={originalPrice} discount={discountPrice} setOriginal={setOriginalPrice} setDiscount={setDiscountPrice} onSubmit={publishProduct} />
    <Dialog open={pickupOpen} onOpenChange={setPickupOpen}><DialogContent className="rounded-[28px] sm:max-w-md"><DialogHeader><DialogTitle className="font-heading text-2xl font-black">核销取餐码</DialogTitle><DialogDescription className="text-base">请让学生出示 6 位数字取餐码。</DialogDescription></DialogHeader><Input value={pickupCode} onChange={(e) => setPickupCode(e.target.value)} className="h-16 rounded-2xl text-center text-2xl font-black tracking-[.3em]" placeholder="482619" maxLength={6} />{pickupMessage && <p className={`rounded-2xl p-4 text-sm font-bold ${pickupMessage.startsWith('核销') ? 'bg-[#e2efd7] text-[#52704b]' : 'bg-[#ffe5dc] text-[#a34f39]'}`}>{pickupMessage}</p>}<DialogFooter><Button onClick={verifyPickup} className="w-full rounded-full">确认核销</Button></DialogFooter></DialogContent></Dialog>
  </main>;
}

function ProductCard({ product, rank, favorite, onFavorite, onOpen }: { product: Product; rank: number; favorite: boolean; onFavorite: () => void; onOpen: () => void }) {
  return <article className="paper-card group overflow-hidden rounded-[26px] border border-border bg-card"><div className="relative aspect-[4/3] overflow-hidden bg-secondary"><button onClick={onOpen} className="h-full w-full"><img src={product.image} alt={product.name} className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.04]" /></button><button onClick={onFavorite} aria-label={favorite ? '取消收藏' : '收藏'} className="absolute right-3 top-3 grid size-9 place-items-center rounded-full bg-white/92 text-primary shadow-sm"><Heart className={`size-4.5 ${favorite ? 'fill-current' : ''}`} /></button><span className="absolute bottom-3 left-3 rounded-full bg-white/92 px-3 py-1.5 text-sm font-bold text-[#6d594b]">{rank === 0 ? '最合口味' : rank === 1 ? '离你很近' : `${product.taste}口味`}</span></div><button onClick={onOpen} className="block w-full p-4.5 text-left"><p className="truncate text-sm text-muted-foreground">{product.shop}</p><h3 className="mt-1.5 font-heading text-xl font-black">{product.name}</h3><div className="mt-3 flex flex-wrap gap-3 text-sm text-muted-foreground"><span className="flex items-center gap-1"><MapPin className="size-3.5" />{product.distance} km</span><span className="flex items-center gap-1"><Clock3 className="size-3.5" />{product.pickup}</span></div><div className="mt-4 flex items-end justify-between"><div><strong className="font-heading text-2xl font-black text-primary">¥ {product.price.toFixed(1)}</strong><span className="ml-2 text-sm text-muted-foreground line-through">¥ {product.original}</span></div><Badge className="rounded-full border-0 bg-[#e3efd8] text-[#57744f] hover:bg-[#e3efd8]">剩 {product.left} 份</Badge></div></button></article>;
}

function StudentOrders({ orders, onView }: { orders: { id: number; productId: number; code: string; status: string; created: string }[]; onView: (p: Product) => void }) {
  return <section className="mx-auto max-w-5xl px-5 py-10 sm:px-8"><DoodleTitle eyebrow="我的订单" title="待领取的好味道" note="到店后出示取餐码，领取完成后商家会为你核销。" /><div className="mt-7 space-y-4">{orders.map((order) => { const product = products.find((p) => p.id === order.productId)!; return <article key={order.id} className="paper-card grid gap-5 rounded-[28px] border border-border bg-card p-5 sm:grid-cols-[110px_1fr_auto] sm:items-center"><img src={product.image} alt="" className="h-28 w-full rounded-[20px] object-cover sm:w-28" /><div><div className="flex items-center gap-2"><Badge className="rounded-full border-0 bg-[#fff0bd] text-[#8a6725] hover:bg-[#fff0bd]">{order.status}</Badge><span className="text-sm text-muted-foreground">{order.created}</span></div><h2 className="mt-3 font-heading text-xl font-black">{product.name}</h2><p className="mt-1 text-sm text-muted-foreground">{product.shop} · {product.pickup}</p></div><button onClick={() => onView(product)} className="rounded-[20px] border-2 border-dashed border-[#efc79f] bg-[#fff5e4] px-6 py-4 text-center"><p className="text-sm font-bold text-muted-foreground">取餐码</p><p className="mt-1 font-heading text-2xl font-black tracking-[.12em]">{order.code}</p></button></article>; })}</div><div className="mt-8 rounded-[24px] bg-[#e5efd9] p-5"><p className="font-bold text-[#56734e]">温馨提醒</p><p className="mt-1 text-sm leading-6 text-[#697c64]">如果临时无法领取，请尽早取消，让这份食物有机会被其他同学带走。</p></div></section>;
}

function StudentProfile({ taste, setTaste, taboos, setTaboos, onSave }: { taste: '清淡' | '麻辣'; setTaste: (v: '清淡' | '麻辣') => void; taboos: string[]; setTaboos: (v: string[]) => void; onSave: () => void }) {
  const allTaboos = ['花生', '海鲜', '香菜', '乳制品'];
  return <section className="mx-auto max-w-4xl px-5 py-10 sm:px-8"><DoodleTitle eyebrow="我的口味" title="让推荐更懂你的胃" note="这些信息只用于筛选食物与控制预算，不会作为公开身份标签。" /><div className="paper-card mt-7 rounded-[30px] border border-border bg-card p-6 sm:p-8"><div className="flex items-center gap-4 border-b border-border pb-6"><span className="grid size-16 place-items-center rounded-[22px] bg-[#ffe2d2] text-primary"><UserRound className="size-8" /></span><div><h2 className="font-heading text-xl font-black">林小满</h2><p className="mt-1 text-sm text-muted-foreground">澳门校园 · 20260018</p></div></div><div className="grid gap-7 pt-7 md:grid-cols-2"><div><label className="text-base font-bold">喜欢的口味</label><div className="mt-3 flex gap-3">{(['清淡','麻辣'] as const).map((item) => <button key={item} onClick={() => setTaste(item)} className={`preference-pill ${taste === item ? 'preference-pill-active' : ''}`}>{item === '清淡' ? '🥬' : '🌶️'} {item}</button>)}</div></div><div><label className="text-base font-bold">每月生活费</label><Input defaultValue="1500" className="mt-3 h-12 rounded-2xl px-4 text-base" /></div><div className="md:col-span-2"><label className="text-base font-bold">饮食禁忌</label><p className="mt-1 text-sm text-muted-foreground">选中的食材不会出现在首页推荐里。</p><div className="mt-3 flex flex-wrap gap-3">{allTaboos.map((item) => { const active = taboos.includes(item); return <button key={item} onClick={() => setTaboos(active ? taboos.filter((x) => x !== item) : [...taboos, item])} className={`preference-pill ${active ? 'preference-pill-active' : ''}`}>{active && <Check className="size-4" />}{item}</button>; })}</div></div></div><Button onClick={onSave} className="mt-8 w-full rounded-full sm:w-auto">保存并更新推荐</Button></div></section>;
}

function MerchantDashboard({ onPublish, onPrice }: { onPublish: () => void; onPrice: () => void }) {
  return <section className="mx-auto max-w-7xl px-5 py-10 sm:px-8"><div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><DoodleTitle eyebrow="暖食档 · 今日经营" title="晚餐时段快开始啦" note="还有 10 份食物可以在关店前找到新主人。" /><Button onClick={onPublish} className="w-fit rounded-full"><Plus className="size-4" />发布今日商品</Button></div><div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><MiniStat label="今日成交" value="27 份" tint="peach" /><MiniStat label="减少浪费" value="18.6 kg" tint="green" /><MiniStat label="今日增收" value="¥ 286" tint="yellow" /><MiniStat label="回头客" value="64%" tint="peach" /></div><div className="mt-5 grid gap-5 lg:grid-cols-[1.15fr_.85fr]"><div className="paper-card rounded-[28px] border border-border bg-card p-6"><div className="flex items-center justify-between"><div><h2 className="font-heading text-xl font-black">今日订单走势</h2><p className="mt-1 text-sm text-muted-foreground">18:00 后预计迎来领取高峰</p></div><span className="text-3xl">📈</span></div><div className="mt-8 flex h-48 items-end gap-3">{[24,31,28,43,52,67,77,69,83,72,54,36].map((h, i) => <div key={i} className="flex h-full flex-1 items-end"><div style={{ height: `${h}%` }} className={`w-full rounded-t-xl ${i > 7 ? 'bg-[#f3c9a6]' : 'bg-[#92b97f]'}`} /></div>)}</div><div className="mt-3 flex justify-between text-sm text-muted-foreground"><span>10:00</span><span>14:00</span><span>18:00</span><span>22:00</span></div></div><div className="paper-card rounded-[28px] border border-[#edcfac] bg-[#fff2d8] p-6"><div className="flex items-center gap-3"><span className="text-3xl">🧮</span><div><p className="text-sm font-bold text-primary">价格小助手</p><h2 className="font-heading text-xl font-black">便当建议调到 ¥9.9</h2></div></div><p className="mt-5 leading-7 text-muted-foreground">距离领取结束还有 2 小时。按最近成交情况，调整后预计售罄率为 92%。</p><div className="mt-5 flex gap-2"><span className="rounded-full bg-white/70 px-3 py-2 text-sm">原价 ¥28</span><span className="rounded-full bg-white/70 px-3 py-2 text-sm">当前 ¥12</span></div><Button onClick={onPrice} className="mt-6 w-full rounded-full">采用 ¥9.9</Button></div></div></section>;
}

function MerchantProducts({ onPublish }: { onPublish: () => void }) {
  return <section className="mx-auto max-w-6xl px-5 py-10 sm:px-8"><div className="flex items-end justify-between"><DoodleTitle eyebrow="商品管理" title="今天正在售卖" note="所有商品到期后会自动下架。" /><Button onClick={onPublish} className="rounded-full"><Plus className="size-4" />发布商品</Button></div><div className="paper-card mt-7 overflow-hidden rounded-[28px] border border-border bg-card">{products.slice(0,4).map((p, i) => <div key={p.id} className="grid gap-4 border-b border-border p-4 last:border-0 sm:grid-cols-[72px_1fr_auto_auto] sm:items-center"><img src={p.image} alt="" className="size-18 rounded-[16px] object-cover" /><div><h2 className="font-heading text-lg font-black">{p.name}</h2><p className="mt-1 text-sm text-muted-foreground">{p.pickup} · ¥{p.price.toFixed(1)}</p></div><p className="font-bold">库存 {p.left}</p><Badge className={`w-fit rounded-full border-0 ${i === 2 ? 'bg-[#ffe5da] text-[#a75038]' : 'bg-[#e3efd8] text-[#55734e]'} hover:bg-[#e3efd8]`}>{i === 2 ? '建议调价' : '状态良好'}</Badge></div>)}</div></section>;
}

function MerchantPickup({ onOpen }: { onOpen: () => void }) {
  return <section className="mx-auto max-w-5xl px-5 py-10 sm:px-8"><DoodleTitle eyebrow="订单核销" title="让同学带走这份好味道" note="输入 6 位取餐码，核对商品后完成领取。" /><div className="mt-8 grid gap-5 md:grid-cols-[.9fr_1.1fr]"><button onClick={onOpen} className="paper-card rounded-[30px] border border-border bg-[#fff1d7] p-8 text-left"><span className="text-5xl">🎟️</span><h2 className="mt-6 font-heading text-2xl font-black">输入取餐码</h2><p className="mt-2 leading-7 text-muted-foreground">演示码：482619</p><span className="mt-7 inline-flex items-center gap-1 font-bold text-primary">开始核销 <ChevronRight className="size-4" /></span></button><div className="paper-card rounded-[30px] border border-border bg-card p-6"><h2 className="font-heading text-xl font-black">待领取订单</h2><div className="mt-5 space-y-3">{products.slice(0,3).map((p, i) => <div key={p.id} className="flex items-center gap-3 rounded-[20px] bg-secondary/65 p-3"><img src={p.image} alt="" className="size-14 rounded-[14px] object-cover" /><div className="min-w-0 flex-1"><p className="truncate font-bold">{p.name}</p><p className="text-sm text-muted-foreground">取餐码 *** {['619','482','705'][i]}</p></div><span className="text-sm font-bold text-primary">待领取</span></div>)}</div></div></div></section>;
}

function AdminDashboard() {
  return <section className="mx-auto max-w-7xl px-5 py-10 sm:px-8"><DoodleTitle eyebrow="平台概览" title="今天，食物被好好接住了" note="数据均为脱敏汇总，不展示经济困难学生身份。" /><div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><MiniStat label="平台注册用户" value="1,286" tint="peach" /><MiniStat label="累计订单" value="3,842" tint="green" /><MiniStat label="本月帮扶领取" value="426 次" tint="yellow" /><MiniStat label="安全拦截" value="18 条" tint="peach" /></div><div className="mt-5 grid gap-5 lg:grid-cols-[1.2fr_.8fr]"><div className="paper-card rounded-[28px] border border-border bg-card p-6"><div className="flex items-center justify-between"><div><h2 className="font-heading text-xl font-black">近 7 日领取趋势</h2><p className="mt-1 text-sm text-muted-foreground">推荐点击率稳定在 31.6%</p></div><BarChart3 className="size-6 text-[#7ea56d]" /></div><div className="mt-8 flex h-52 items-end gap-5">{[42,58,49,71,67,82,76].map((h, i) => <div key={i} className="flex h-full flex-1 flex-col items-center justify-end gap-2"><div style={{ height: `${h}%` }} className="w-full max-w-12 rounded-t-xl bg-[#f19a72]" /><span className="text-sm text-muted-foreground">{['一','二','三','四','五','六','日'][i]}</span></div>)}</div></div><div className="paper-card rounded-[28px] border border-border bg-[#e5efd9] p-6"><span className="text-4xl">🌏</span><h2 className="mt-5 font-heading text-xl font-black">本月减少浪费</h2><p className="mt-3 font-heading text-5xl font-black text-[#5b7a53]">386 kg</p><p className="mt-4 leading-7 text-[#657d61]">来自 23 家校园周边商户，共完成 892 次剩余食物领取。</p></div></div></section>;
}

function AdminAudit({ approved, onAudit }: { approved: number[]; onAudit: (id: number, pass: boolean) => void }) {
  return <section className="mx-auto max-w-6xl px-5 py-10 sm:px-8"><DoodleTitle eyebrow="商家审核" title="守好每一家店的入口" note="核对营业执照、店铺位置和联系方式后再开放发布权限。" /><div className="mt-7 space-y-4">{pendingMerchants.map((m) => <article key={m.id} className="paper-card grid gap-5 rounded-[28px] border border-border bg-card p-6 md:grid-cols-[64px_1fr_auto] md:items-center"><span className="grid size-16 place-items-center rounded-[20px] bg-[#fff0d5] text-3xl">🏪</span><div><div className="flex flex-wrap items-center gap-2"><h2 className="font-heading text-xl font-black">{m.shop}</h2>{approved.includes(m.id) ? <Badge className="rounded-full border-0 bg-[#e2efd7] text-[#54724d] hover:bg-[#e2efd7]">已处理</Badge> : <Badge className="rounded-full border-0 bg-[#fff0bd] text-[#8a6725] hover:bg-[#fff0bd]">待审核</Badge>}</div><p className="mt-2 text-sm text-muted-foreground">负责人：{m.owner} · {m.location} · {m.submitted}</p><button className="mt-3 flex items-center gap-1 text-sm font-bold text-primary"><BookOpen className="size-4" />查看营业执照</button></div>{!approved.includes(m.id) && <div className="flex gap-2"><Button onClick={() => onAudit(m.id, false)} variant="outline" className="rounded-full">驳回</Button><Button onClick={() => onAudit(m.id, true)} className="rounded-full">通过</Button></div>}</article>)}</div></section>;
}

function RiskLogs({ logs, onResolve }: { logs: typeof riskSeed; onResolve: (id: number) => void }) {
  return <section className="mx-auto max-w-6xl px-5 py-10 sm:px-8"><DoodleTitle eyebrow="安全日志" title="把风险挡在发布之前" note="规则检查价格、有效期和违规内容，需要时再交给管理员复核。" /><div className="paper-card mt-7 overflow-hidden rounded-[28px] border border-border bg-card">{logs.map((log) => <div key={log.id} className="grid gap-4 border-b border-border p-5 last:border-0 md:grid-cols-[130px_1fr_auto] md:items-center"><div><Badge className={`rounded-full border-0 ${log.type === '价格异常' ? 'bg-[#ffe4d8] text-[#a34e37]' : 'bg-[#fff0bd] text-[#866423]'} hover:bg-[#ffe4d8]`}>{log.type}</Badge></div><div><h2 className="font-heading text-lg font-black">{log.item} · {log.shop}</h2><p className="mt-1 text-sm text-muted-foreground">{log.detail}</p></div><div className="flex items-center gap-3"><span className="text-sm font-bold text-muted-foreground">{log.level}</span>{log.level === '待复核' && <Button onClick={() => onResolve(log.id)} variant="outline" className="rounded-full">标记处理</Button>}</div></div>)}</div></section>;
}

function AdminUsers({ disabled, onToggle }: { disabled: number[]; onToggle: (id: number) => void }) {
  const users = [{ id: 1, name: '林小满', account: '20260018', role: '学生', orders: 12 }, { id: 2, name: '暖食档', account: 'nuanshi01', role: '商家', orders: 286 }, { id: 3, name: '校园帮帮忙', account: '20260107', role: '学生', orders: 3 }, { id: 4, name: '麦香屋', account: 'maixiang', role: '商家', orders: 164 }];
  return <section className="mx-auto max-w-6xl px-5 py-10 sm:px-8"><DoodleTitle eyebrow="用户管理" title="让社区保持友好可靠" note="只在有明确违规记录时停用账号，所有操作都会保留记录。" /><div className="paper-card mt-7 overflow-hidden rounded-[28px] border border-border bg-card">{users.map((user) => { const inactive = disabled.includes(user.id); return <div key={user.id} className="grid gap-4 border-b border-border p-5 last:border-0 md:grid-cols-[56px_1fr_auto_auto] md:items-center"><span className={`grid size-14 place-items-center rounded-[18px] text-2xl ${user.role === '商家' ? 'bg-[#fff0d5]' : 'bg-[#e4efd9]'}`}>{user.role === '商家' ? '🏪' : '🎒'}</span><div><div className="flex items-center gap-2"><h2 className="font-heading text-lg font-black">{user.name}</h2><Badge variant="outline" className="rounded-full">{user.role}</Badge></div><p className="mt-1 text-sm text-muted-foreground">账号 {user.account} · 累计订单 {user.orders}</p></div><span className={`w-fit rounded-full px-3 py-1.5 text-sm font-bold ${inactive ? 'bg-[#ffe4da] text-[#a24e38]' : 'bg-[#e3efd8] text-[#55734e]'}`}>{inactive ? '已停用' : '正常'}</span><Button onClick={() => onToggle(user.id)} variant="outline" className="rounded-full">{inactive ? '恢复账号' : '停用账号'}</Button></div>; })}</div></section>;
}

function AuthDialog({ open, setOpen, role, setRole, mode, setMode, onLogin, onNotice }: { open: boolean; setOpen: (v: boolean) => void; role: Role; setRole: (v: Role) => void; mode: 'login' | 'register' | 'reset'; setMode: (v: 'login' | 'register' | 'reset') => void; onLogin: (role: Role) => void; onNotice: (s: string) => void }) {
  return <Dialog open={open} onOpenChange={setOpen}><DialogContent className="max-h-[92vh] overflow-y-auto rounded-[30px] sm:max-w-md"><div className="mb-1"><Logo /></div><DialogHeader><DialogTitle className="font-heading text-2xl font-black">{mode === 'login' ? '欢迎回来' : mode === 'register' ? '加入食愿' : '找回密码'}</DialogTitle><DialogDescription className="text-base">{mode === 'login' ? '选择身份进入对应的演示空间。' : mode === 'register' ? '学生可直接注册，商家提交后需等待审核。' : '验证身份后，演示密码将重置为 123456。'}</DialogDescription></DialogHeader><div className="grid grid-cols-3 gap-2 rounded-[18px] bg-secondary p-1.5">{(['student','merchant','admin'] as Role[]).map((item) => <button key={item} onClick={() => setRole(item)} className={`rounded-[14px] px-2 py-2.5 text-sm font-bold ${role === item ? 'bg-card text-primary shadow-sm' : 'text-muted-foreground'}`}>{item === 'student' ? '学生' : item === 'merchant' ? '商家' : '管理员'}</button>)}</div><div className="space-y-3">{mode === 'register' && role === 'student' && <Input className="h-12 rounded-2xl px-4" placeholder="学校" />}{mode === 'register' && role === 'merchant' && <><Input className="h-12 rounded-2xl px-4" placeholder="店铺名称" /><label className="flex h-12 cursor-pointer items-center justify-center rounded-2xl border border-dashed border-[#e4bc94] bg-[#fff5e6] text-sm font-bold text-primary">上传营业执照<input type="file" className="sr-only" accept="image/*" /></label></>}<Input className="h-12 rounded-2xl px-4" placeholder={role === 'student' ? '学号' : role === 'merchant' ? '商家账号' : '管理员账号'} defaultValue={mode === 'login' && role === 'admin' ? 'admin' : ''} />{mode !== 'reset' && <Input type="password" className="h-12 rounded-2xl px-4" placeholder="密码" defaultValue={mode === 'login' ? '123456' : ''} />}{mode === 'reset' && <><Input className="h-12 rounded-2xl px-4" placeholder={role === 'student' ? '姓名' : '店名'} /><Input className="h-12 rounded-2xl px-4" placeholder="手机号" /></>}</div><DialogFooter><Button onClick={() => { if (mode === 'login') onLogin(role); else { setOpen(false); onNotice(mode === 'register' ? (role === 'merchant' ? '资料已提交，审核通过后可登录' : '注册成功，可以登录了') : '验证通过，密码已重置为 123456'); } }} className="w-full rounded-full">{mode === 'login' ? '进入食愿' : mode === 'register' ? '提交注册' : '验证并重置'}</Button></DialogFooter><div className="flex justify-center gap-5 text-sm font-bold text-primary"><button onClick={() => setMode(mode === 'register' ? 'login' : 'register')}>{mode === 'register' ? '返回登录' : '注册新账号'}</button><button onClick={() => setMode(mode === 'reset' ? 'login' : 'reset')}>{mode === 'reset' ? '返回登录' : '忘记密码'}</button></div></DialogContent></Dialog>;
}

function PublishDialog({ open, setOpen, success, error, original, discount, setOriginal, setDiscount, onSubmit }: { open: boolean; setOpen: (v: boolean) => void; success: boolean; error: string; original: string; discount: string; setOriginal: (v: string) => void; setDiscount: (v: string) => void; onSubmit: () => void }) {
  return <Dialog open={open} onOpenChange={setOpen}><DialogContent className="max-h-[92vh] overflow-y-auto rounded-[30px] sm:max-w-lg">{!success ? <><DialogHeader><DialogTitle className="font-heading text-2xl font-black">发布今日商品</DialogTitle><DialogDescription className="text-base">填写后会先检查价格、有效期与内容安全。</DialogDescription></DialogHeader><div className="space-y-4"><Input className="h-12 rounded-2xl px-4" defaultValue="暖食便当惊喜盒" placeholder="商品名称" /><Textarea className="min-h-24 rounded-2xl p-4" defaultValue="今日现做便当，含一份主食与两款配菜。" /><div className="grid grid-cols-2 gap-3"><div><label className="mb-2 block text-sm font-bold">原价</label><Input value={original} onChange={(e) => setOriginal(e.target.value)} className="h-12 rounded-2xl px-4" /></div><div><label className="mb-2 block text-sm font-bold">折扣价</label><Input value={discount} onChange={(e) => setDiscount(e.target.value)} className="h-12 rounded-2xl px-4" /></div></div><div className="grid grid-cols-2 gap-3"><Input className="h-12 rounded-2xl px-4" defaultValue="8" placeholder="数量" /><Input className="h-12 rounded-2xl px-4" defaultValue="20:30" placeholder="截止时间" /></div><label className="flex h-24 cursor-pointer items-center justify-center rounded-[22px] border-2 border-dashed border-[#e4c29f] bg-[#fff7e8] text-sm font-bold text-primary">＋ 上传商品照片<input type="file" className="sr-only" accept="image/*" /></label>{error && <div className="flex gap-2 rounded-[20px] bg-[#ffe5db] p-4 text-sm font-bold leading-6 text-[#a34f38]"><CircleAlert className="mt-0.5 size-5 shrink-0" />{error}</div>}<button onClick={() => { setOriginal('28'); setDiscount('35'); }} className="text-sm font-bold text-muted-foreground underline decoration-dotted underline-offset-4">填入价格异常案例</button></div><DialogFooter><Button onClick={onSubmit} className="w-full rounded-full"><ShieldCheck className="size-4" />检查并发布</Button></DialogFooter></> : <div className="py-6 text-center"><span className="mx-auto grid size-16 place-items-center rounded-full bg-[#e2efd7] text-[#57754f]"><Check className="size-8" /></span><DialogTitle className="mt-5 font-heading text-2xl font-black">商品发布成功</DialogTitle><DialogDescription className="mt-2 text-base">价格、有效期与内容检查均已通过。</DialogDescription><Button onClick={() => setOpen(false)} className="mt-6 w-full rounded-full">完成</Button></div>}</DialogContent></Dialog>;
}

function MobileNav({ role, studentView, merchantView, adminView, onStudent, onMerchant, onAdmin }: { role: Role; studentView: StudentView; merchantView: MerchantView; adminView: AdminView; onStudent: (v: StudentView) => void; onMerchant: (v: MerchantView) => void; onAdmin: (v: AdminView) => void }) {
  const studentItems: { key: StudentView; label: string; icon: typeof House }[] = [{ key: 'home', label: '发现', icon: House }, { key: 'orders', label: '订单', icon: ShoppingBag }, { key: 'community', label: '愿望', icon: TreePine }, { key: 'profile', label: '我的', icon: UserRound }];
  const merchantItems: { key: MerchantView; label: string; icon: typeof House }[] = [{ key: 'shop', label: '概览', icon: House }, { key: 'products', label: '商品', icon: PackageCheck }, { key: 'pickup', label: '核销', icon: ClipboardCheck }];
  const adminItems: { key: AdminView; label: string; icon: typeof House }[] = [{ key: 'dashboard', label: '数据', icon: BarChart3 }, { key: 'audit', label: '审核', icon: Store }, { key: 'users', label: '用户', icon: UsersRound }, { key: 'risk', label: '安全', icon: ShieldCheck }];
  const items = role === 'student' ? studentItems : role === 'merchant' ? merchantItems : adminItems;
  const active = role === 'student' ? studentView : role === 'merchant' ? merchantView : adminView;
  return <nav className={`fixed inset-x-0 bottom-0 z-50 grid border-t border-border bg-card/95 px-2 pb-[max(8px,env(safe-area-inset-bottom))] pt-2 backdrop-blur md:hidden ${items.length === 4 ? 'grid-cols-4' : 'grid-cols-3'}`}>{items.map((item) => { const Icon = item.icon; return <button key={item.key} onClick={() => role === 'student' ? onStudent(item.key as StudentView) : role === 'merchant' ? onMerchant(item.key as MerchantView) : onAdmin(item.key as AdminView)} className={`flex flex-col items-center gap-1 py-1 text-xs font-bold ${active === item.key ? 'text-primary' : 'text-muted-foreground'}`}><Icon className="size-5" />{item.label}</button>; })}</nav>;
}
