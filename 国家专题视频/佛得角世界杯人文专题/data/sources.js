export const sources = [
  {
    id: "aljazeera-cpv-argentina",
    title: "Cape Verde qualify for World Cup Round of 32, set up date with Argentina",
    publisher: "Al Jazeera",
    date: "2026-06-27",
    url: "https://www.aljazeera.com/sports/2026/6/27/cape-verde-qualify-for-world-cup-round-of-32-set-up-date-with-argentina",
    role: "current-football-fact"
  },
  {
    id: "aljazeera-last32-schedule",
    title: "Which teams are in World Cup last 32 knockouts and what is the schedule?",
    publisher: "Al Jazeera",
    date: "2026-06-28",
    url: "https://www.aljazeera.com/sports/2026/6/28/which-teams-are-in-world-cup-last-32-knockouts-and-what-is-the-schedule",
    role: "current-football-fact"
  },
  {
    id: "olympics-cpv-round32",
    title: "Cabo Verde fairytale continues as Blue Sharks reach Round of 32",
    publisher: "Olympics.com",
    date: "2026-06-27",
    url: "https://www.olympics.com/en/news/fifa-world-cup-2026-cabo-verde-football-round-of-32",
    role: "current-football-context"
  },
  {
    id: "fifa-cpv-profile",
    title: "Cabo Verde team profile",
    publisher: "FIFA",
    date: "2026",
    url: "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/cabo-verde-team-profile-history",
    role: "team-profile"
  },
  {
    id: "worldbank-cabo-verde",
    title: "Cabo Verde country overview",
    publisher: "World Bank",
    date: "2026",
    url: "https://www.worldbank.org/ext/en/country/caboverde",
    role: "economy-development"
  },
  {
    id: "unesco-morna",
    title: "Morna, musical practice of Cabo Verde",
    publisher: "UNESCO Intangible Cultural Heritage",
    date: "2019",
    url: "https://ich.unesco.org/en/RL/morna-musical-practice-of-cabo-verde-01469",
    role: "culture"
  },
  {
    id: "visit-caboverde-islands",
    title: "The islands of Cabo Verde",
    publisher: "Visit Cabo Verde",
    date: "2026",
    url: "https://www.visit-caboverde.com/en/islands",
    role: "geography-tourism"
  },
  {
    id: "factbook-cabo-verde",
    title: "Cabo Verde country profile",
    publisher: "World Factbook",
    date: "2026",
    url: "https://theworldfactbook.org/country/cabo-verde.html",
    role: "country-data"
  },
  {
    id: "cntraveler-soccer-roots",
    title: "To understand Cape Verde's soccer roots, head to the beach",
    publisher: "Conde Nast Traveler",
    date: "2026-05",
    url: "https://www.cntraveler.com/story/to-understand-cape-verdes-soccer-roots-head-to-the-beach",
    role: "human-interest-context"
  },
  {
    id: "euronews-pico-lopes",
    title: "Who is Pico Lopes, the unlikely Cape Verde World Cup hero recruited through LinkedIn?",
    publisher: "Euronews",
    date: "2026-06-16",
    url: "https://www.euronews.com/2026/06/16/who-is-pico-lopes-the-unlikely-cape-verde-world-cup-hero-recruited-through-linkedin",
    role: "football-diaspora-context"
  }
];

export const claims = [
  {
    id: "snapshot-date",
    text: "截至2026年6月28日，佛得角已经进入2026世界杯32强淘汰赛。",
    sourceIds: ["aljazeera-cpv-argentina", "aljazeera-last32-schedule"]
  },
  {
    id: "argentina-opponent",
    text: "佛得角32强对手是卫冕冠军阿根廷。",
    sourceIds: ["aljazeera-cpv-argentina"]
  },
  {
    id: "three-draws",
    text: "佛得角以三场平局、小组第二身份出线。",
    sourceIds: ["aljazeera-cpv-argentina", "olympics-cpv-round32"]
  },
  {
    id: "morna-unesco",
    text: "Morna 是佛得角标志性音乐实践，并被列入联合国教科文组织非遗名录。",
    sourceIds: ["unesco-morna"]
  },
  {
    id: "tourism-economy",
    text: "旅游是佛得角经济的重要支柱，国家也面临耕地有限和资源有限的现实。",
    sourceIds: ["worldbank-cabo-verde", "factbook-cabo-verde"]
  }
];
