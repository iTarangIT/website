// Static demo data for the NBFC partner dashboard.
// TODO: replace with real data source before production.

export type LeadStatus = "New" | "AI-Qualified" | "Under Review" | "Approved";

export type VehicleType = "E-Rickshaw" | "E-Loader";

export type TranscriptLine = {
  speaker: "AI" | "Driver";
  text: string;
};

export type ExtractionField = {
  label: string;
  value: string;
  revealAfterLineIndex: number;
};

export type Lead = {
  id: string;
  name: string;
  age: number;
  city: string;
  phoneMasked: string;
  language: string;
  score: number;
  vehicle: VehicleType;
  loanAmount: number;
  status: LeadStatus;
  transcript: TranscriptLine[];
  extraction: ExtractionField[];
  finalScore: number;
  finalVerdict: "QUALIFIED" | "REVIEW" | "DISQUALIFIED";
};

export const demoProfile = {
  name: "Demo NBFC Pvt Ltd",
  tagline: "Partner Account",
  aumLabel: "₹15.4 Cr",
  activeLoans: 2987,
  npaPct: 1.8,
};

export const kpis = {
  batteriesFinanced: 3142,
  activeLoans: 2987,
  portfolioAumLabel: "₹15.4 Cr",
  npa: {
    itarang: 1.8,
    industry: 6.2,
  },
  leadToDisbursement: {
    value: "4 hrs",
    comparison: "vs 3 days industry",
  },
  recoveryRate: {
    value: "78%",
    comparison: "vs ~30% industry",
  },
};

export const dialerStats = {
  callsMade: 184,
  qualified: 92,
  hotLeads: 24,
  disqualified: 68,
};

export const leads: Lead[] = [
  {
    id: "lead-01",
    name: "Ramesh Kumar",
    age: 34,
    city: "Lucknow",
    phoneMasked: "+91 98XXX XX742",
    language: "Hindi",
    score: 82,
    vehicle: "E-Rickshaw",
    loanAmount: 65000,
    status: "AI-Qualified",
    transcript: [
      { speaker: "AI", text: "Namaste Ramesh ji, main iTarang se Priya bol rahi hoon. Kya aap loan ke baare mein baat kar sakte hain?" },
      { speaker: "Driver", text: "Haan ji, boliye." },
      { speaker: "AI", text: "Aap kitne saalon se e-rickshaw chala rahe hain?" },
      { speaker: "Driver", text: "Teen saal se." },
      { speaker: "AI", text: "Roz ka kitna kama lete hain approximately?" },
      { speaker: "Driver", text: "700-800 rupaye, kabhi 900 bhi." },
      { speaker: "AI", text: "Aapka current loan koi chal raha hai?" },
      { speaker: "Driver", text: "Nahi, pehle ek liya tha, time pe chuka diya." },
      { speaker: "AI", text: "Bahut accha. Aap kis area mein chalate hain mostly?" },
      { speaker: "Driver", text: "Hazratganj se Charbagh route." },
      { speaker: "AI", text: "Theek hai, main aapki details verify karke wapas call karungi. Dhanyawad." },
    ],
    extraction: [
      { label: "Identity verified", value: "Ramesh Kumar, 34", revealAfterLineIndex: 1 },
      { label: "Years of experience", value: "3 years", revealAfterLineIndex: 3 },
      { label: "Daily earnings claimed", value: "₹700–900", revealAfterLineIndex: 5 },
      { label: "Past loan history", value: "Closed on time", revealAfterLineIndex: 7 },
      { label: "Operating route", value: "Hazratganj – Charbagh (consistent)", revealAfterLineIndex: 9 },
      { label: "Sentiment", value: "Cooperative", revealAfterLineIndex: 10 },
    ],
    finalScore: 82,
    finalVerdict: "QUALIFIED",
  },
  {
    id: "lead-02",
    name: "Suresh Yadav",
    age: 41,
    city: "Kanpur",
    phoneMasked: "+91 97XXX XX318",
    language: "Hindi",
    score: 76,
    vehicle: "E-Loader",
    loanAmount: 78000,
    status: "Under Review",
    transcript: [
      { speaker: "AI", text: "Namaste Suresh ji, main iTarang se bol rahi hoon. Aapke loan application ke liye kuch sawal poochne hain." },
      { speaker: "Driver", text: "Haan, bataiye." },
      { speaker: "AI", text: "Aap e-loader kitne samay se chala rahe hain?" },
      { speaker: "Driver", text: "Pichhle chaar saal se." },
      { speaker: "AI", text: "Monthly income roughly kya hoti hai?" },
      { speaker: "Driver", text: "Twenty-five se thirty thousand ke beech." },
      { speaker: "AI", text: "Koi purani EMI chal rahi hai abhi?" },
      { speaker: "Driver", text: "Ek personal loan chal raha hai, next month khatam hoga." },
      { speaker: "AI", text: "Aap kaunsa area cover karte hain delivery ke liye?" },
      { speaker: "Driver", text: "Kanpur industrial area, mostly." },
      { speaker: "AI", text: "Theek hai ji, hum aapka profile review karke wapas sampark karenge." },
    ],
    extraction: [
      { label: "Identity verified", value: "Suresh Yadav, 41", revealAfterLineIndex: 1 },
      { label: "Years of experience", value: "4 years", revealAfterLineIndex: 3 },
      { label: "Monthly earnings claimed", value: "₹25,000–30,000", revealAfterLineIndex: 5 },
      { label: "Past loan history", value: "Active EMI — closing next month", revealAfterLineIndex: 7 },
      { label: "Operating route", value: "Kanpur industrial belt", revealAfterLineIndex: 9 },
      { label: "Sentiment", value: "Transparent", revealAfterLineIndex: 10 },
    ],
    finalScore: 76,
    finalVerdict: "REVIEW",
  },
  {
    id: "lead-03",
    name: "Mohd. Aslam",
    age: 29,
    city: "Delhi NCR",
    phoneMasked: "+91 99XXX XX521",
    language: "Hindi",
    score: 88,
    vehicle: "E-Rickshaw",
    loanAmount: 58000,
    status: "Approved",
    transcript: [
      { speaker: "AI", text: "Assalamu alaikum Aslam bhai, main iTarang se Priya. Kya abhi do minute baat kar sakte hain?" },
      { speaker: "Driver", text: "Walaikum assalam. Haan bataiye." },
      { speaker: "AI", text: "Aap kitne saalon se driving kar rahe hain?" },
      { speaker: "Driver", text: "Paanch saal ho gaye." },
      { speaker: "AI", text: "Roz ka earning kitna rehta hai?" },
      { speaker: "Driver", text: "Average 900 rupaye, weekend pe 1100 tak." },
      { speaker: "AI", text: "Koi chalu loan hai?" },
      { speaker: "Driver", text: "Nahi, sab clear hai." },
      { speaker: "AI", text: "Aap kaunsa route cover karte hain?" },
      { speaker: "Driver", text: "Noida sector 18 se Botanical Garden metro." },
      { speaker: "AI", text: "Shukriya Aslam bhai. Aapki application proceed kar di gayi hai." },
    ],
    extraction: [
      { label: "Identity verified", value: "Mohd. Aslam, 29", revealAfterLineIndex: 1 },
      { label: "Years of experience", value: "5 years", revealAfterLineIndex: 3 },
      { label: "Daily earnings claimed", value: "₹900–1,100", revealAfterLineIndex: 5 },
      { label: "Past loan history", value: "No active loans", revealAfterLineIndex: 7 },
      { label: "Operating route", value: "Noida 18 – Botanical Garden", revealAfterLineIndex: 9 },
      { label: "Sentiment", value: "Confident", revealAfterLineIndex: 10 },
    ],
    finalScore: 88,
    finalVerdict: "QUALIFIED",
  },
  {
    id: "lead-04",
    name: "Vinod Sharma",
    age: 46,
    city: "Patna",
    phoneMasked: "+91 96XXX XX904",
    language: "Hindi",
    score: 54,
    vehicle: "E-Rickshaw",
    loanAmount: 72000,
    status: "New",
    transcript: [
      { speaker: "AI", text: "Namaste Vinod ji, main iTarang se call kar rahi hoon loan application ke liye." },
      { speaker: "Driver", text: "Haan, bataiye jaldi, main busy hoon." },
      { speaker: "AI", text: "Bas do minute chahiye. Aap kitne saalon se chala rahe hain?" },
      { speaker: "Driver", text: "Ek saal ho gaya, shayad." },
      { speaker: "AI", text: "Roz ka earning kitna hota hai approximately?" },
      { speaker: "Driver", text: "Pata nahi ji, kabhi 400, kabhi 800." },
      { speaker: "AI", text: "Kya koi purana loan tha?" },
      { speaker: "Driver", text: "Haan tha, thoda default ho gaya tha, ab settle kar diya." },
      { speaker: "AI", text: "Aap kaunsa area mein chalate hain?" },
      { speaker: "Driver", text: "Kabhi Kankarbagh, kabhi station ki taraf. Fix nahi hai." },
      { speaker: "AI", text: "Theek hai Vinod ji, hum aapko wapas call karenge." },
    ],
    extraction: [
      { label: "Identity verified", value: "Vinod Sharma, 46", revealAfterLineIndex: 1 },
      { label: "Years of experience", value: "~1 year (low)", revealAfterLineIndex: 3 },
      { label: "Daily earnings claimed", value: "₹400–800 (inconsistent)", revealAfterLineIndex: 5 },
      { label: "Past loan history", value: "Prior default, settled", revealAfterLineIndex: 7 },
      { label: "Operating route", value: "Patna — variable", revealAfterLineIndex: 9 },
      { label: "Sentiment", value: "Hesitant", revealAfterLineIndex: 10 },
    ],
    finalScore: 54,
    finalVerdict: "DISQUALIFIED",
  },
  {
    id: "lead-05",
    name: "Rakesh Verma",
    age: 37,
    city: "Kolkata",
    phoneMasked: "+91 98XXX XX255",
    language: "Hindi",
    score: 79,
    vehicle: "E-Loader",
    loanAmount: 80000,
    status: "AI-Qualified",
    transcript: [
      { speaker: "AI", text: "Namaste Rakesh ji, main iTarang se Priya bol rahi hoon." },
      { speaker: "Driver", text: "Ji, namaste." },
      { speaker: "AI", text: "Aap kitne saal se e-loader chala rahe hain?" },
      { speaker: "Driver", text: "Do saal. Pehle truck driver tha." },
      { speaker: "AI", text: "Monthly earning kitna hota hai?" },
      { speaker: "Driver", text: "Thirty thousand ke aas paas." },
      { speaker: "AI", text: "Koi active EMI hai currently?" },
      { speaker: "Driver", text: "Nahi ji, ek baar tha, closed ho gaya." },
      { speaker: "AI", text: "Kaunsa route zyada use karte hain?" },
      { speaker: "Driver", text: "Howrah se Salt Lake, daily delivery." },
      { speaker: "AI", text: "Bahut accha. Hum details verify karke aapko update karenge." },
    ],
    extraction: [
      { label: "Identity verified", value: "Rakesh Verma, 37", revealAfterLineIndex: 1 },
      { label: "Years of experience", value: "2 years (+ truck driving)", revealAfterLineIndex: 3 },
      { label: "Monthly earnings claimed", value: "~₹30,000", revealAfterLineIndex: 5 },
      { label: "Past loan history", value: "Closed on time", revealAfterLineIndex: 7 },
      { label: "Operating route", value: "Howrah – Salt Lake", revealAfterLineIndex: 9 },
      { label: "Sentiment", value: "Cooperative", revealAfterLineIndex: 10 },
    ],
    finalScore: 79,
    finalVerdict: "QUALIFIED",
  },
  {
    id: "lead-06",
    name: "Sanjay Singh",
    age: 31,
    city: "Lucknow",
    phoneMasked: "+91 95XXX XX612",
    language: "Hindi",
    score: 84,
    vehicle: "E-Rickshaw",
    loanAmount: 60000,
    status: "AI-Qualified",
    transcript: [
      { speaker: "AI", text: "Namaste Sanjay ji, main iTarang se bol rahi hoon." },
      { speaker: "Driver", text: "Haan ji, boliye." },
      { speaker: "AI", text: "Kitne saalon se e-rickshaw chala rahe hain?" },
      { speaker: "Driver", text: "Saade teen saal." },
      { speaker: "AI", text: "Roz ki kamai kitni hoti hai?" },
      { speaker: "Driver", text: "800 se 1000 ke beech, rozana." },
      { speaker: "AI", text: "Koi purani EMI ya loan chalu hai?" },
      { speaker: "Driver", text: "Nahi ji, mera record clean hai." },
      { speaker: "AI", text: "Aap kaunsa route prefer karte hain?" },
      { speaker: "Driver", text: "Alambagh se Aminabad mostly." },
      { speaker: "AI", text: "Shukriya. Aapki application pe jaldi decision aayega." },
    ],
    extraction: [
      { label: "Identity verified", value: "Sanjay Singh, 31", revealAfterLineIndex: 1 },
      { label: "Years of experience", value: "3.5 years", revealAfterLineIndex: 3 },
      { label: "Daily earnings claimed", value: "₹800–1,000", revealAfterLineIndex: 5 },
      { label: "Past loan history", value: "No defaults", revealAfterLineIndex: 7 },
      { label: "Operating route", value: "Alambagh – Aminabad", revealAfterLineIndex: 9 },
      { label: "Sentiment", value: "Confident", revealAfterLineIndex: 10 },
    ],
    finalScore: 84,
    finalVerdict: "QUALIFIED",
  },
  {
    id: "lead-07",
    name: "Pankaj Gupta",
    age: 39,
    city: "Delhi NCR",
    phoneMasked: "+91 97XXX XX088",
    language: "Hindi",
    score: 68,
    vehicle: "E-Rickshaw",
    loanAmount: 55000,
    status: "Under Review",
    transcript: [
      { speaker: "AI", text: "Namaste Pankaj ji, main iTarang se Priya. Kaise hain aap?" },
      { speaker: "Driver", text: "Theek hoon ji." },
      { speaker: "AI", text: "Aap kitne saalon se e-rickshaw chala rahe hain?" },
      { speaker: "Driver", text: "Do saal." },
      { speaker: "AI", text: "Roz ki earning kitni hoti hai?" },
      { speaker: "Driver", text: "600-700 ke aas paas." },
      { speaker: "AI", text: "Koi loan chal raha hai abhi?" },
      { speaker: "Driver", text: "Haan, ek gold loan chal raha hai, chhota sa." },
      { speaker: "AI", text: "Aap kaunsa area cover karte hain?" },
      { speaker: "Driver", text: "Gurgaon sector 14 se cyber hub." },
      { speaker: "AI", text: "Theek hai ji, hum details verify kar ke update denge." },
    ],
    extraction: [
      { label: "Identity verified", value: "Pankaj Gupta, 39", revealAfterLineIndex: 1 },
      { label: "Years of experience", value: "2 years", revealAfterLineIndex: 3 },
      { label: "Daily earnings claimed", value: "₹600–700", revealAfterLineIndex: 5 },
      { label: "Past loan history", value: "Active gold loan", revealAfterLineIndex: 7 },
      { label: "Operating route", value: "Gurgaon 14 – Cyber Hub", revealAfterLineIndex: 9 },
      { label: "Sentiment", value: "Calm", revealAfterLineIndex: 10 },
    ],
    finalScore: 68,
    finalVerdict: "REVIEW",
  },
  {
    id: "lead-08",
    name: "Arjun Pal",
    age: 27,
    city: "Patna",
    phoneMasked: "+91 98XXX XX173",
    language: "Hindi",
    score: 81,
    vehicle: "E-Rickshaw",
    loanAmount: 45000,
    status: "New",
    transcript: [
      { speaker: "AI", text: "Namaste Arjun ji, main iTarang se bol rahi hoon, kya abhi baat ho sakti hai?" },
      { speaker: "Driver", text: "Haan ji, boliye." },
      { speaker: "AI", text: "Aap kitne time se driving kar rahe hain?" },
      { speaker: "Driver", text: "Do saal ho gaye, pehle bhaiya ke saath kaam karta tha." },
      { speaker: "AI", text: "Daily earning approximately kitni hoti hai?" },
      { speaker: "Driver", text: "750-900 rupaye daily." },
      { speaker: "AI", text: "Kya koi EMI chal rahi hai currently?" },
      { speaker: "Driver", text: "Nahi ji, pehla loan le raha hoon." },
      { speaker: "AI", text: "Aap mostly kaunsa route chalate hain?" },
      { speaker: "Driver", text: "Boring Road se Ashok Rajpath, fix route hai." },
      { speaker: "AI", text: "Bahut accha Arjun ji. Aapki application process karte hain." },
    ],
    extraction: [
      { label: "Identity verified", value: "Arjun Pal, 27", revealAfterLineIndex: 1 },
      { label: "Years of experience", value: "2 years", revealAfterLineIndex: 3 },
      { label: "Daily earnings claimed", value: "₹750–900", revealAfterLineIndex: 5 },
      { label: "Past loan history", value: "First-time borrower", revealAfterLineIndex: 7 },
      { label: "Operating route", value: "Boring Road – Ashok Rajpath", revealAfterLineIndex: 9 },
      { label: "Sentiment", value: "Cooperative", revealAfterLineIndex: 10 },
    ],
    finalScore: 81,
    finalVerdict: "QUALIFIED",
  },
];
