"""وحدة تحميل البيانات من Yahoo Finance لأسهم البورصة المصرية (EGX) - النسخة الاحترافية."""
import warnings
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd

warnings.filterwarnings("ignore")

# ============================================================
# قاعدة بيانات شاملة لجميع أسهم EGX (229 سهم - محدثة من EGX)
# المصدر: stockanalysis.com + EGX
# ============================================================
EGX_STOCKS = {
    "COMI.CA": "Commercial International Bank Egypt (CIB) S.A.E.",
    "SWDY.CA": "El Sewedy Electric Company",
    "TMGH.CA": "Talaat Moustafa Group Holding",
    "ETEL.CA": "Telecom Egypt Company",
    "EGAL.CA": "Egypt Aluminum",
    "MFPC.CA": "Misr Fertilizer Production Company",
    "HDBK.CA": "Housing and Development Bank- Egypt (S.A.E)",
    "QNBE.CA": "Qatar National Bank",
    "ABUK.CA": "Abu Qir Fertilizers & Chemical Industries Company (S.A.E)",
    "EAST.CA": "Eastern Company S.A.E",
    "ALCN.CA": "Alexandria Container&Cargo Handling Company",
    "ORAS.CA": "Orascom Construction PLC",
    "EFIH.CA": "e-finance for Digital and Financial Investments S.A.E.",
    "ADIB.CA": "Abu Dhabi Islamic Bank - Egypt - S.A.E",
    "EMFD.CA": "Emaar Misr for Development Company (S.A.E.)",
    "FWRY.CA": "Fawry for Banking Technology and Electronic Payments S.A.E.",
    "SCTS.CA": "Suez Canal Company for Technology Settling (S.A.E)",
    "ORHD.CA": "Orascom Development Egypt S.A.E.",
    "OCDI.CA": "Sixth of October for Development and Investment Company \"SODIC\" (S.A.E.)",
    "CANA.CA": "Suez Canal Bank (S.A.E)",
    "EFID.CA": "Edita Food Industries Company (S.A.E)",
    "PHDC.CA": "Palm Hills Developments S.A.E.",
    "VLMR.CA": "Valmore Holding S.A.E.",
    "VLMRA.CA": "Valmore Holding S.A.E.",
    "GPPL.CA": "Golden Pyramids Plaza S.A.E.",
    "JUFO.CA": "Juhayna Food Industries S.A.E.",
    "HRHO.CA": "EFG Holding Company S.A.E",
    "HELI.CA": "Heliopolis Co. for Housing & Development",
    "FERC.CA": "Ferchem Misr for fertilizers and chemicals S.A.E",
    "BTFH.CA": "Beltone Holding S.A.E",
    "RAYA.CA": "Raya Holding Company for Financial Investments (S.A.E)",
    "CIEB.CA": "Credit Agricole - Egypt Bank (S.A.E.)",
    "GBCO.CA": "GB Corp",
    "FAIT.CA": "Faisal Islamic Bank of Egypt",
    "FAITA.CA": "Faisal Islamic Bank of Egypt",
    "EXPA.CA": "Export Development Bank of Egypt (S.A.E.)",
    "IRON.CA": "Egyptian Iron and Steel Company",
    "ARCC.CA": "Arabian Cement Company S.A.E.",
    "EGCH.CA": "Egyptian Chemical Industries",
    "BIOC.CA": "GlaxoSmithKline S.A.E",
    "SCEM.CA": "Sinai Cement Co. (S.A.E)",
    "CLHO.CA": "Cleopatra Hospitals Group S.A.E.",
    "CCAP.CA": "QALA For Financial Investments",
    "MCQE.CA": "Misr Cement (Qena) Company (S.A.E)",
    "VALU.CA": "U Consumer Finance S.A.E.",
    "MBSC.CA": "Misr Beni Suef Cement Co. S.A.E",
    "PHAR.CA": "Egyptian International Pharmaceutical Industries Company",
    "TAQA.CA": "TAQA Arabia S.A.E.",
    "SKPC.CA": "Sidi Kerir Petrochemicals Co.",
    "AMES.CA": "Alexandria New Medical Center",
    "CIRA.CA": "Cairo For Investment And Real Estate Developments-CIRA Education",
    "MTIE.CA": "MM Group for Industry and International Trade S.A.E.",
    "EFIC.CA": "Egyptian Financial and Industrial SAE",
    "POUL.CA": "Cairo Poultry Company S.A.E.",
    "ORWE.CA": "Oriental Weavers Carpets Company (S.A.E)",
    "EGTS.CA": "Egyptian Resorts Company (S.A.E)",
    "AMOC.CA": "Alexandria Mineral Oils Company",
    "SAUD.CA": "alBaraka Bank Egypt S.A.E.",
    "NIPH.CA": "EI- Nile Co. for Pharmaceuticals and Chemical Industries",
    "EGSA.CA": "The Egyptian Satellite Company Nilesat",
    "MASR.CA": "Madinet Masr For Housing and Development",
    "MOIL.CA": "Maridive and Oil Services S.A.E.",
    "UBEE.CA": "The United Bank",
    "ATQA.CA": "Misr National Steel - Ataqa",
    "MHOT.CA": "Misr Hotels Company",
    "EGBE.CA": "Egyptian Gulf Bank (S.A.E)",
    "KORA.CA": "Korra for Energy and Investment Projects (S.A.E.)",
    "TALM.CA": "Taaleem Management Services Company S.A.E.",
    "ISPH.CA": "Ibnsina Pharma",
    "CSAG.CA": "Canal Shipping Agencies Company",
    "CICH.CA": "CI Capital Holding For Financial Investments (S.A.E)",
    "RMDA.CA": "Tenth of Ramadan for Pharmaceutical Industries and Diagnostic Reagents (Rameda) (S.A.E)",
    "BINV.CA": "B Investments Holding S.A.E.",
    "OIH.CA": "Orascom Investment Holding S.A.E.",
    "IFAP.CA": "International Company for Agricultural Crops",
    "AMIA.CA": "Arab Moltaqa Investments Company",
    "MOIN.CA": "Mohandes Insurance Company",
    "MPRC.CA": "Egyptian Media Production City",
    "MPCI.CA": "Memphis Pharmaceuticals & Chemical Industries",
    "ZMID.CA": "Zahraa El Maadi Investment and Development Company SAE",
    "MIPH.CA": "MINAPHARM Pharmaceuticals",
    "PRDC.CA": "Pioneers Properties For Urban Development - PRE Group",
    "ISMQ.CA": "Iron & Steel for Mines & Quarries",
    "OLFI.CA": "Obour Land for Food Industries S.A.E.",
    "EGAS.CA": "Egypt Gas Company SAE",
    "SUGR.CA": "Delta Sugar Company",
    "BONY.CA": "Bonyan for Development and Trade",
    "PHTV.CA": "Pyramisa Hotels & Resorts",
    "AXPH.CA": "Alexandria Co. For Pharmaceuticals & Chemical Industries",
    "CPCI.CA": "Kahira Pharmaceuticals & Chemical Industries Company",
    "DOMT.CA": "Arabian Food Industries Company (DOMTY) - S.A.E",
    "NINH.CA": "Nozha International Hospital",
    "ELEC.CA": "Electro Cable Egypt",
    "SPIN.CA": "Alexandria Spinning & Weaving Co.",
    "GOUR.CA": "Gourmet Egypt.Com Foods",
    "SPHT.CA": "El Shams Pyramids Co. For Hotels & Touristic Projects S.A.E",
    "NAPR.CA": "National Printing Company S.A.E.",
    "ACAP.CA": "A Capital Holding",
    "ENGC.CA": "Industrial Engineering Company for Construction and Development (ICON) (S.A.E.)",
    "ARAB.CA": "Arab Developers Holding",
    "SVCE.CA": "South Valley Cement Company",
    "OCPH.CA": "October Pharma S.A.E",
    "CNFN.CA": "Contact Financial Holding S.A.E.",
    "AFMC.CA": "Alexandria Flour Mills",
    "MICH.CA": "Misr Chemical Industries Co.",
    "GSSC.CA": "General Co. For Silos & Storage",
    "DSCW.CA": "Dice For Ready-Made Garments (SAE)",
    "KABO.CA": "El-Nasr Clothing & Textiles Co. (KABO)",
    "WCDF.CA": "Middle & West Delta Flour Mills",
    "AMER.CA": "Amer Group Holding Company S.A.E.",
    "MFSC.CA": "Egypt Free Shops Co.",
    "OFH.CA": "O B Financial Holding S.A.E",
    "GDWA.CA": "Gadwa for Industrial Development",
    "SAIB.CA": "Société Arabe Internationale de Banque S.A.E",
    "UNIT.CA": "United Co. for Housing & Development - S.A.E.",
    "ACGC.CA": "Arabia Cotton Ginning Company",
    "UEFM.CA": "Upper Egypt Mills Company J.S.C",
    "SDTI.CA": "SHARM DREAMS Co. for Touristic Investment S.A.E",
    "KZPC.CA": "Kafr El Zayat For Pesticides & Chemicals Co.(S.A.E)",
    "AJWA.CA": "AJWA For Food Industries Co. Egypt",
    "ADCI.CA": "The Arab Drug Company",
    "CRST.CA": "Creast Mark For Contracting And Real Estate Development",
    "ELKA.CA": "Cairo for Housing and Development Company (S.A.E)",
    "GTWL.CA": "Golden Textiles & Clothes Wool",
    "ACTF.CA": "Act Financial",
    "ASCM.CA": "ASEC Company for Mining ASCOM, S.A.E",
    "ELSH.CA": "Al-Shams Company for Housing and Urban Development",
    "DAPH.CA": "Development & Engineering Consultants",
    "ISMA.CA": "Ismailia / Misr Poultry Company S.A.E",
    "INFI.CA": "Ismailia National Co. for Food Industries",
    "ALRA.CA": "Atlas for Investment & Food Industries",
    "CFGH.CA": "Concrete Fashion Group For Commercial and Industrial investments S.A.E",
    "ICFC.CA": "International Company for Fertilizers and Chemicals S.A.E",
    "ZEOT.CA": "Extracted Oil & Derivatives Co.",
    "ATLC.CA": "Al Tawfeek Leasing Company",
    "LCSW.CA": "Lecico Egypt (S.A.E.)",
    "NAHO.CA": "Naeem Holding Company For Investments (S.A.E - Free Zone)",
    "ETRS.CA": "Egyptian Transport & Commercial Services Co. -EGYTRANS NOSCO",
    "GPIM.CA": "GPI for Urban Growth",
    "EDFM.CA": "East Delta Flour Mills",
    "ACAMD.CA": "Arab Co.,for asset management and development",
    "SMFR.CA": "Samad Misr EGYFERT.S.A.E",
    "NARE.CA": "Naeem Real Estate Holding Group",
    "MPCO.CA": "Mansoura Poultry co.S.A.E",
    "MILS.CA": "North Cairo Flour Mills",
    "CEFM.CA": "Middle Egypt Flour Mills",
    "GGRN.CA": "Go Green For Agricultural Investment And Development",
    "PHGC.CA": "Premium Healthcare Group",
    "MAAL.CA": "Marseille Almasreia Alkhalegeya For Holding Investment SAE",
    "IDRE.CA": "Ismailia Development and Real Estate Co",
    "EALR.CA": "Arab Company For Land Reclamation",
    "AALR.CA": "General Company For Land Reclamation, Development & Reconstruction",
    "ADPC.CA": "The Arab Dairy Products Co.",
    "MOSC.CA": "Misr Oils & Soap",
    "EHDR.CA": "Egyptians for Housing & Development Co.",
    "RACC.CA": "Raya Customer Experience",
    "WKOL.CA": "Wadi Kom Ombo For Land Reclamation Co.",
    "ICID.CA": "International Co. For Investment & Development",
    "GGCC.CA": "Giza General - Contracting and Real Estate Investment S.A.E",
    "ECAP.CA": "Al Ezz Ceramics & Porcelain Co.",
    "KRDI.CA": "AlKhair River for Development Agricultural Investment and Environmental Services",
    "SNFC.CA": "Sharkia National Company for Food Security",
    "ODIN.CA": "ODIN Investments (S.A.E)",
    "DTPP.CA": "Delta Co. For Printing & Packaging S.A.E",
    "MENA.CA": "Mena for Touristic & Real Estate Investment",
    "CAED.CA": "Cairo Educational Services SAE",
    "SCFM.CA": "South Cairo and Giza Flour Mills and Bakeries Company",
    "CERA.CA": "The Arab Ceramic Co.",
    "PRCL.CA": "The General Company for Ceramic and Porcelain Products",
    "NCCW.CA": "Nasr Company for Civil Works",
    "IEEC.CA": "Industrial & Engineering Projects",
    "DEIN.CA": "Delta Insurance Company",
    "NHPS.CA": "National Company for Housing Professional Syndicates SAE",
    "MBEG.CA": "M.B For Engineering & Contracting",
    "OBRI.CA": "El-Ebour Co. for Real Estate Investment S.A.E.",
    "SEIG.CA": "Saudi Egyptian Investment & Finance Co. S.A.E",
    "SEIGA.CA": "Saudi Egyptian Investment & Finance Co. S.A.E",
    "SIPC.CA": "Sabaa International Company for Pharmaceutical and Chemical Industry",
    "AIHC.CA": "Arabia Investments Holding",
    "MEPA.CA": "Medical Packaging Company",
    "UEGC.CA": "El-Saeed Company for Contracting and Real Estate Investment \"SCCD\" (S.A.E.)",
    "COSG.CA": "Cairo Oil & Soap Company",
    "ALUM.CA": "Arab Aluminum Company (S.A.E)",
    "NDRL.CA": "National Drilling Company",
    "AIDC.CA": "Arabia for Investment and Development S.A.E.",
    "LUTS.CA": "Lotus For Agricultural Investments And Development",
    "AMII.CA": "Arabian Metal Industries and Industrial Investments",
    "EBSC.CA": "Osool ESB Securities Brokerage",
    "RREI.CA": "Arab Real Estate Investment Co.",
    "GTEX.CA": "GTEX for Commercial and Industrial Investments S.A.E",
    "AFDI.CA": "Al Ahly for Development & Investment",
    "POCO.CA": "Port Said Containers And Cargo Handling Co.",
    "RTVC.CA": "Remco Tourism Villages Construction",
    "PRMH.CA": "Prime Holding S.A.E",
    "MCRO.CA": "Macro Group Pharmaceuticals (Macro Capital) S.A.E",
    "ASPI.CA": "Aspire Capital Holding for Financial Investments",
    "UNIP.CA": "Universal For Paper and Packaging Materials",
    "KWIN.CA": "El Kahera El Watania Investment",
    "MOED.CA": "The Egyptian Modern Education Systems, S.A.E.",
    "APSW.CA": "Unirab Polvara Spinning & Weaving Co.",
    "ICLE.CA": "International Company for Leasing S.A.E.",
    "TANM.CA": "Tanmiya For Real Estate Investment (S.A.E)",
    "MEGM.CA": "Middle East Glass Manufacturing Company S.A.E.",
    "TYCN.CA": "Tycoon Holding Company For Financial Investments",
    "RUBX.CA": "Rubex International for Plastic and Acrylic Manufacturing",
    "ROTO.CA": "Rowad Tourism Company",
    "SPMD.CA": "Speed Medical Co",
    "EASB.CA": "Egyptian Arabian Company (Themar) for securities Brokerage EAC",
    "RAKT.CA": "Rakta Paper Manufacturing Company",
    "GRCA.CA": "Grand Capital for Financial Investments",
    "EEII.CA": "Arab Engineering Industries",
    "AREH.CA": "Real Estate Egyptian Consortium S.A.E",
    "TWSA.CA": "Tawasoa For Factoring",
    "CCRS.CA": "Gulf Canadian Company for Arab Real Estate Investment",
    "EPCO.CA": "Egypt for Poultry",
    "TRTO.CA": "Trans Oceans Tours",
    "FCMD.CA": "International Company For Medical Industries S.A.E.",
    "GIHD.CA": "Gharbia Islamic Housing Development Company",
    "ELWA.CA": "El Wadi for International and Investment Development SAE",
    "ELNA.CA": "El Nasr Manufacturing Agricultural Crops S.A.E",
    "DGTZ.CA": "Digitize for Investment And Technology",
    "DCCC.CA": "Damietta Container & Cargo Handling Co.",
    "MMAT.CA": "Marsa Marsa Alam For Tourism Development SAE",
    "NEDA.CA": "Northern Upper Egypt For Development & Agricultural Production Co.",
    "EPPK.CA": "El Ahram Co. For Printing And Packaging SAE",
    "GMCI.CA": "GMC Group For Industrial Commercial & Financial Investments",
    "EOSB.CA": "El Orouba Securities Brokerage",
    "CPME.CA": "Catalyst Partners",
    "COPR.CA": "Copper for Commercial Investment & Real Estate Development",
}

# أسماء عربية لأهم الأسهم (للعرض بالعربي حيثما توفر)
AR_NAMES = {
    "COMI.CA": "البنك التجاري الدولي (CIB)",
    "SWDY.CA": "السويدي إليكتريك",
    "TMGH.CA": "طلعت مصطفى القابضة",
    "ETEL.CA": "المصرية للاتصالات",
    "EGAL.CA": "مصر للألومنيوم",
    "MFPC.CA": "مصر لإنتاج الأسمدة",
    "HDBK.CA": "بنك التعمير والإسكان",
    "QNBE.CA": "بنك قطر الوطني",
    "ABUK.CA": "أبو قير للأسمدة",
    "EAST.CA": "الشرقية للدخان",
    "ALCN.CA": "الإسكندرية للحاويات",
    "ORAS.CA": "أوراسكوم للإنشاء",
    "EFIH.CA": "إي فاينانس",
    "ADIB.CA": "مصرف أبو ظبي الإسلامي",
    "EMFD.CA": "إعمار مصر",
    "FWRY.CA": "فوري",
    "ORHD.CA": "أوراسكوم للتنمية",
    "OCDI.CA": "سوديك",
    "PHDC.CA": "بالم هيلز",
    "CIEB.CA": "بنك كريدي أجريكول",
    "HRHO.CA": "إي إف جي هيرميس",
    "HELI.CA": "مصر الجديدة للإسكان",
    "BTFH.CA": "بلتون القابضة",
    "JUFO.CA": "جهينة",
    "AMOC.CA": "أموك",
    "DOMT.CA": "دومتي",
    "ELEC.CA": "الكابلات الكهربائية",
    "EFID.CA": "إيديتا",
    "CCAP.CA": "القلعة",
    "GBCO.CA": "جي بي كورب",
    "CIRA.CA": "القاهرة للاستثمار",
    "ORWE.CA": "النساجون الشرقيون",
    "CLHO.CA": "كليوباترا",
    "ARAB.CA": "المطورون العرب",
    "TALM.CA": "تعليم",
    "RAYA.CA": "راية القابضة",
    "MNHD.CA": "مدينة مصر",
    "MASR.CA": "مدينة مصر للإسكان",
    "AJWA.CA": "أجوا",
    "KZPC.CA": "كفر الزيات",
}

# مكونات EGX30 (أكبر 30 سهم من حيث القيمة السوقية)
EGX30_TICKERS = list(EGX_STOCKS.keys())[:30]

# ============================================================
# صناديق الاستثمار المتداولة (ETFs):
# ⚠️ تم التحقق عملياً (سبتمبر 2026): لا يوجد أي صندوق/ETF مصري
# متاح على Yahoo Finance مجاناً (فُحص 19 رمزاً وكلها فشلت).
# الصناديق المصرية تُتداول في البورصة لكن بياناتها غير مجانية.
# لتتبع الصناديق استخدم تطبيق ثاندر مباشرة أو موقع EGX.
# ============================================================
EGX_ETFS = {}

# ============================================================
# تصنيف القطاعات للأسهم الرئيسية (للفلترة والتحليل القطاعي)
# الأسهم غير المذكورة = "أخرى"
# ============================================================
SECTORS = {
    # بنوك ومالية
    "COMI.CA": "بنوك", "QNBE.CA": "بنوك", "ADIB.CA": "بنوك", "HDBK.CA": "بنوك",
    "CIEB.CA": "بنوك", "GBCO.CA": "بنوك", "FAIT.CA": "بنوك", "FAITA.CA": "بنوك",
    "EXPA.CA": "بنوك", "SAUD.CA": "بنوك", "EGBE.CA": "بنوك", "UBEE.CA": "بنوك",
    "CANA.CA": "بنوك", "AAIB.CA": "بنوك", "ALBR.CA": "بنوك",
    "EFIH.CA": "مالية ووساطة", "FWRY.CA": "مالية ووساطة", "VALU.CA": "مالية ووساطة",
    "HRHO.CA": "مالية ووساطة", "BTFH.CA": "مالية ووساطة", "CCAP.CA": "مالية ووساطة",
    "PRMH.CA": "مالية ووساطة", "ASPI.CA": "مالية ووساطة", "EBSC.CA": "مالية ووساطة",
    "MIDR.CA": "مالية ووساطة", "TYCN.CA": "مالية ووساطة", "GRCA.CA": "مالية ووساطة",
    "SCTS.CA": "مالية ووساطة", "MFIN.CA": "مالية ووساطة", "SUGR.CA": "مالية ووساطة",
    # عقارات
    "TMGH.CA": "عقارات", "EMFD.CA": "عقارات", "PHDC.CA": "عقارات", "OCDI.CA": "عقارات",
    "ORHD.CA": "عقارات", "HELI.CA": "عقارات", "MNHD.CA": "عقارات", "MASR.CA": "عقارات",
    "ARAB.CA": "عقارات", "MFHC.CA": "عقارات", "SDTI.CA": "عقارات", "PLLC.CA": "عقارات",
    "GPPL.CA": "عقارات", "ALCN.CA": "خدمات ولوجستيات", "TALM.CA": "تعليم",
    # اتصالات وتكنولوجيا
    "ETEL.CA": "اتصالات وتكنولوجيا", "FWRY.CA": "مالية ووساطة",
    "RAYA.CA": "اتصالات وتكنولوجيا", "DGTZ.CA": "اتصالات وتكنولوجيا",
    "EGSA.CA": "اتصالات وتكنولوجيا", "MTIE.CA": "اتصالات وتكنولوجيا",
    "ISPH.CA": "اتصالات وتكنولوجيا",
    # أسمدة وكيميائيات
    "MFPC.CA": "أسمدة وكيمياويات", "ABUK.CA": "أسمدة وكيمياويات",
    "SKPC.CA": "أسمدة وكيمياويات", "EFIC.CA": "أسمدة وكيمياويات",
    "EGCH.CA": "أسمدة وكيمياويات", "FERC.CA": "أسمدة وكيمياويات",
    "KZPC.A": "أسمدة وكيمياويات", "RMDA.CA": "أسمدة وكيمياويات",
    "SIIN.CA": "أسمدة وكيمياويات",
    # أسمنت وبناء
    "ARCC.CA": "أسمنت وبناء", "SCEM.CA": "أسمنت وبناء", "MBSC.CA": "أسمنت وبناء",
    "MCQE.CA": "أسمنت وبناء", "ORAS.CA": "أسمنت وبناء", "TORA.CA": "أسمنت وبناء",
    # صناعة وتصنيع
    "SWDY.CA": "صناعة وتصنيع", "EGAL.CA": "صناعة وتصنيع", "ORWE.CA": "صناعة وتصنيع",
    "ELEC.CA": "صناعة وتصنيع", "AMOK.CA": "صناعة وتصنيع", "CSAG.CA": "صناعة وتصنيع",
    "ATQA.CA": "صناعة وتصنيع", "IRON.CA": "صناعة وتصنيع", "AMIN.CA": "صناعة وتصنيع",
    "SPMD.CA": "صناعة وتصنيع", "UNIP.CA": "صناعة وتصنيع", "RUBX.CA": "صناعة وتصنيع",
    "EGAB.CA": "صناعة وتصنيع", "EPRC.CA": "صناعة وتصنيع",
    # أغذية ومشروبات
    "EFID.CA": "أغذية ومشروبات", "JUFO.CA": "أغذية ومشروبات", "DOMT.CA": "أغذية ومشروبات",
    "POUL.CA": "أغذية ومشروبات", "EPCO.CA": "أغذية ومشروبات", "EKHO.CA": "أغذية ومشروبات",
    "ODIN.CA": "أغذية ومشروبات", "EGAL.CA": "صناعة وتصنيع",
    # أدوية وصحة
    "PHAR.CA": "أدوية وصحة", "BIOC.CA": "أدوية وصحة", "NIPH.CA": "أدوية وصحة",
    "AMPH.CA": "أدوية وصحة", "ISPH.CA": "أدوية وصحة", "CLHO.CA": "أدوية وصحة",
    "AMES.CA": "أدوية وصحة", "SPMD.CA": "صناعة وتصنيع", "MCRO.CA": "أدوية وصحة",
    # نفط وغاز وطاقة
    "AMOC.CA": "نفط وغاز وطاقة", "MOIL.CA": "نفط وغاز وطاقة", "TAQA.CA": "نفط وغاز وطاقة",
    "GBCO.CA": "بنوك", "PETR.CA": "نفط وغاز وطاقة", "ADRI.CA": "نفط وغاز وطاقة",
    "MPRC.CA": "نفط وغاز وطاقة", "ELNA.CA": "نفط وغاز وطاقة",
    # ترفيه وفنادق وسياحة
    "EGTS.CA": "ترفيه وفنادق", "MHOT.CA": "ترفيه وفنادق", "ROTO.CA": "ترفيه وفنادق",
    "SAUD.CA": "بنوك", "HELI.CA": "عقارات", "TRTO.CA": "ترفيه وفنادق",
    "MMAT.CA": "ترفيه وفنادق", "SHRM.CA": "ترفيه وفنادق", "EGSH.CA": "ترفيه وفنادق",
}

# القطاعات المتاحة (للعرض)
SECTOR_LIST = sorted(set(SECTORS.values())) + ["أخرى"]

# دالة الحصول على قطاع سهم
def get_sector(symbol: str) -> str:
    return SECTORS.get(symbol, "أخرى")

# كل الأسهم المتاحة (أسهم + صناديق)
ALL_SYMBOLS = {**EGX_STOCKS, **EGX_ETFS}
ALL_TICKERS = list(ALL_SYMBOLS.keys())

# دالة البحث الشاملة (أسهم + صناديق)
def search_all(query: str):
    """بحث في الأسهم والصناديق بالاسم العربي أو الإنجليزي أو الرمز."""
    q = query.strip().lower()
    if not q:
        return []
    results = []
    for sym, name in ALL_SYMBOLS.items():
        ar_name = AR_NAMES.get(sym, "")
        if (q in sym.lower().replace(".ca", "") or
            q in name.lower() or
            (ar_name and q in ar_name.lower())):
            results.append((sym, name))
    return results[:15]


PERIOD_MAP = {
    "1 شهر": "1mo",
    "3 شهور": "3mo",
    "6 شهور": "6mo",
    "سنة واحدة": "1y",
    "سنتان": "2y",
    "5 سنوات": "5y",
    "10 سنوات": "10y",
    "الكل": "max",
}

# فترات التداول المناسبة لأسهم البورصة المصرية
INTERVAL_MAP = {
    "يومي (1d) - تداول سوينغ": "1d",
    "أسبوعي (1wk) - استثمار متوسط": "1wk",
    "شهري (1mo) - استثمار طويل": "1mo",
}

INTERVAL_PERIOD_MAP = {
    "1d": None,
    "1wk": None,
    "1mo": None,
}


def get_stock_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """تحميل بيانات الأسعار التاريخية لسهم واحد (يدعم المضاربة اللحظية)."""
    # للمضاربة: غيّر الفترة تلقائياً حسب الفاصل
    eff_period = INTERVAL_PERIOD_MAP.get(interval, period) if interval != "1d" else period
    if eff_period is None:
        eff_period = period
    # المحاولة الأولى بالفاصل المطلوب
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=eff_period, interval=interval, auto_adjust=True)
        if df is not None and not df.empty and "Close" in df.columns:
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
            if not df.empty:
                return df
        # إذا فشل (خاصة EGX لا يدعم اللحظي)، جرّب اليومي كـ fallback
        if interval != "1d":
            df2 = ticker.history(period=period, interval="1d", auto_adjust=True)
            if df2 is not None and not df2.empty:
                df2 = df2[["Open", "High", "Low", "Close", "Volume"]].dropna()
                return df2
        return pd.DataFrame()
    except Exception as e:
        # fallback لليومي عند خطأ tradingPeriods (EGX)
        if interval != "1d":
            try:
                ticker = yf.Ticker(symbol)
                df2 = ticker.history(period=period, interval="1d", auto_adjust=True)
                if df2 is not None and not df2.empty:
                    df2 = df2[["Open", "High", "Low", "Close", "Volume"]].dropna()
                    return df2
            except:
                pass
        print(f"خطأ في تحميل بيانات {symbol}: {e}")
        return pd.DataFrame()


def get_bulk_data(symbols: list, period: str = "3mo", interval: str = "1d", auto_adjust: bool = True) -> dict:
    """
    تحميل بيانات مجمعة لعدة أسهم دفعة واحدة (أسرع بكثير من حلقة).
    ترجع dict {symbol: DataFrame}
    يدعم الفواصل اللحظية للمضاربة (مع fallback لليومي لـ EGX).
    """
    if not symbols:
        return {}
    eff_period = INTERVAL_PERIOD_MAP.get(interval, period) if interval != "1d" else period
    if eff_period is None:
        eff_period = period
    try:
        # yfinance download يدعم قائمة رموز
        data = yf.download(
            tickers=" ".join(symbols),
            period=eff_period,
            interval=interval,
            auto_adjust=auto_adjust,
            progress=False,
            group_by="ticker",
            threads=True,
        )
        # إذا فشل اللحظي لـ EGX، جرّب اليومي
        if (data is None or data.empty) and interval != "1d":
            data = yf.download(
                tickers=" ".join(symbols),
                period=period,
                interval="1d",
                auto_adjust=auto_adjust,
                progress=False,
                group_by="ticker",
                threads=True,
            )
        if data is None or data.empty:
            return {}
        result = {}
        # حالة سهم واحد: data أعمدة عادية
        if len(symbols) == 1:
            sym = symbols[0]
            if "Close" in data.columns or "Open" in data.columns:
                df = data[["Open", "High", "Low", "Close", "Volume"]].dropna()
                result[sym] = df
            return result
        # حالة متعددة: multi-index
        for sym in symbols:
            try:
                if sym in data.columns.get_level_values(0):
                    sub = data[sym].copy()
                    sub = sub[["Open", "High", "Low", "Close", "Volume"]].dropna()
                    if not sub.empty:
                        result[sym] = sub
            except Exception:
                continue
        return result
    except Exception as e:
        if interval != "1d":
            try:
                data = yf.download(
                    tickers=" ".join(symbols),
                    period=period,
                    interval="1d",
                    auto_adjust=auto_adjust,
                    progress=False,
                    group_by="ticker",
                    threads=True,
                )
                if data is not None and not data.empty:
                    # إعادة المعالجة بسرعة
                    result = {}
                    if len(symbols) == 1:
                        sym = symbols[0]
                        if "Close" in data.columns:
                            df = data[["Open","High","Low","Close","Volume"]].dropna()
                            result[sym] = df
                        return result
                    for sym in symbols:
                        try:
                            if sym in data.columns.get_level_values(0):
                                sub = data[sym].copy()
                                sub = sub[["Open","High","Low","Close","Volume"]].dropna()
                                if not sub.empty:
                                    result[sym] = sub
                        except: continue
                    if result:
                        return result
            except:
                pass
        print(f"خطأ bulk: {e}")
        return {}


def get_live_prices(symbols: list) -> pd.DataFrame:
    """جلب آخر الأسعار والتغير اليومي بسرعة (period=2d)."""
    bulk = get_bulk_data(symbols, period="5d")
    rows = []
    for sym, df in bulk.items():
        if len(df) < 2:
            continue
        last = df.iloc[-1]
        prev = df.iloc[-2]
        change = ((last["Close"] - prev["Close"]) / prev["Close"] * 100) if prev["Close"] else 0
        rows.append({
            "الرمز": sym,
            "الاسم": AR_NAMES.get(sym, EGX_STOCKS.get(sym, sym)),
            "السعر": round(float(last["Close"]), 2),
            "التغير%": round(float(change), 2),
            "الحجم": int(last["Volume"]),
            "قيمة_التداول_م": round(float(last["Close"] * last["Volume"]) / 1e6, 2),
            "الإغلاق_السابق": round(float(prev["Close"]), 2),
            "أعلى": round(float(last["High"]), 2),
            "أدنى": round(float(last["Low"]), 2),
        })
    return pd.DataFrame(rows)


def get_ticker_info(symbol: str) -> dict:
    """جلب البيانات الأساسية للشركة."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info if info else {}
    except Exception:
        return {}


_tv_names_cache = None


def _tv_names() -> dict:
    """أسماء الأسهم بالعربية من TradingView (للأسهم غير الموجودة في AR_NAMES)."""
    global _tv_names_cache
    if _tv_names_cache is None:
        try:
            from .tv_data import snapshot
            snap = snapshot()
            _tv_names_cache = {k: v["name_tv"] for k, v in snap.items()} if snap else {}
        except Exception:
            _tv_names_cache = {}
    return _tv_names_cache


def get_company_name(symbol: str) -> str:
    """إرجاع الاسم (عربي منقح أولاً، ثم اسم TradingView العربي، ثم الإنجليزي)."""
    return (AR_NAMES.get(symbol)
            or _tv_names().get(symbol.replace(".CA", ""))
            or ALL_SYMBOLS.get(symbol, symbol.replace(".CA", "")))


def search_stocks(query: str):
    """البحث في قائمة الأسهم."""
    query = query.strip().lower()
    if not query:
        return list(EGX_STOCKS.items())
    return [
        (sym, AR_NAMES.get(sym, name))
        for sym, name in EGX_STOCKS.items()
        if query in sym.lower() or query in name.lower() or query in AR_NAMES.get(sym, "").lower()
    ]
