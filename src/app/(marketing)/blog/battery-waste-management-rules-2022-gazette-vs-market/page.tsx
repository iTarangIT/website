import Image from "next/image";
import { createMetadata } from "@/lib/metadata";
import BlogLayout from "@/components/blog/BlogLayout";

export const metadata = createMetadata({
  title: "Battery Waste Management Rules 2022: Gazette vs Market Claims",
  description:
    "S.O. 958(E) makes battery QR codes optional, not mandatory. What the notifications actually say, and three questions that let you check any compliance claim in ten minutes.",
  path: "/blog/battery-waste-management-rules-2022-gazette-vs-market",
  ogImage: "/images/blog/battery-waste-management-rules-2022-gazette-vs-market.jpg",
});

export default function BatteryWasteManagementRulesGazetteVsMarketArticle() {
  return (
    <BlogLayout
      title="Battery Waste Management Rules 2022: what the gazette says, and what the internet keeps repeating"
      slug="battery-waste-management-rules-2022-gazette-vs-market"
      date="2026-08-25"
      readTime="6 min read"
      category="lifecycle-recycling"
    >
      <p>Last week I read the Battery Waste Management Rules 2022 and its amendments straight from the gazette, instead of from anybody&rsquo;s summary. Three compliance claims I had seen repeated all year turned out to be wrong, and one of them would have had a producer spend money printing QR codes the law does not ask for. This piece is about what the notifications actually say, and how you can check any claim like it yourself in about ten minutes.</p>

      <figure className="my-10">
        <Image
          src="/images/blog/battery-waste-management-rules-2022-gazette-vs-market.jpg"
          alt="The gazette says may. The internet says must. S.O. 958(E) makes the battery QR code optional."
          width={1200}
          height={630}
          priority
          className="h-auto w-full rounded-xl"
        />
        <figcaption>S.O. 958(E) of 24 February 2025 uses the word &ldquo;may&rdquo;. Much of the market has been repeating &ldquo;must&rdquo;.</figcaption>
      </figure>

      <h2>A policy research institute published that QR codes are mandatory. The notification says they are optional.</h2>
      <p>Here is the claim, from a published explainer by an Indian policy research institute: &ldquo;QR codes or barcodes including the producer&rsquo;s EPR registration number must be placed on the batteries, battery packs, equipment and packaging.&rdquo;</p>
      <p>Now here is the notification it is describing. S.O. 958(E), dated 24 February 2025, the Battery Waste Management (Amendment) Rules, 2025, says that producers <strong>may</strong> fulfil the requirements of the relevant clause, subject to providing the information in writing to the Central Pollution Control Board.</p>
      <p>May. Not shall.</p>
      <p>What the amendment actually created is a choice. You may print a barcode or QR code carrying your EPR registration number on the battery, the pack, the equipment it sits in, or the packaging. Or you may simply print the registration number in the product information brochure. Either way you tell CPCB in writing which route you took.</p>
      <p>That is a relaxation. Somebody read it as a new obligation and published the opposite of it.</p>
      <p>I am not picking on one organisation. I checked ten sources across two searches. Not one of them quoted the notification. The one that got closest to the operative clause inverted the verb.</p>

      <h2>Seven of the nine results on page one are government pages, and almost nobody opens them</h2>
      <p>I looked at what actually ranks in India for &ldquo;battery waste management rules 2022&rdquo;. Seven of the nine organic results are government or intergovernmental: CPCB, the CPCB EPR portal, MNRE, the Karnataka pollution board, PIB, an official FAQ PDF, and the IEA.</p>
      <p>The primary sources are right there, at the top, free.</p>
      <p>They still lose, because a gazette notification is written for a court, not for a compliance manager on a Tuesday. So the manager reads a blog. The blog read another blog. And Google&rsquo;s AI Overview on that same page cites seven sources, none of which is a notification, then repeats the same second-hand numbers back to you with more confidence than any of them had.</p>
      <p>That is how a false claim travels. Not through bad faith. Through nobody opening the PDF.</p>

      <h2>Check any claim in ten minutes, using three questions</h2>
      <p>You do not need a lawyer for this. You need the habit.</p>

      <div className="my-8 overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b-2 border-gray-300">
              <th className="py-3 pr-4 font-semibold">Ask this</th>
              <th className="py-3 pr-4 font-semibold">Why it works</th>
              <th className="py-3 font-semibold">A good answer</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-gray-200">
              <td className="py-3 pr-4 align-top font-semibold">What is the S.O. number?</td>
              <td className="py-3 pr-4 align-top">Every rule change in India is a numbered gazette notification. A claim with no number is somebody&rsquo;s opinion.</td>
              <td className="py-3 align-top">&ldquo;S.O. 958(E), 24 February 2025&rdquo;</td>
            </tr>
            <tr className="border-b border-gray-200">
              <td className="py-3 pr-4 align-top font-semibold">Is the verb &ldquo;shall&rdquo; or &ldquo;may&rdquo;?</td>
              <td className="py-3 pr-4 align-top">This single word separates an obligation from an option. It is the most commonly mistranslated thing in compliance writing.</td>
              <td className="py-3 align-top">&ldquo;May. It is an alternative, not a requirement.&rdquo;</td>
            </tr>
            <tr className="border-b border-gray-200">
              <td className="py-3 pr-4 align-top font-semibold">Which notification introduced it?</td>
              <td className="py-3 pr-4 align-top">Rules get amended. A claim can be true of the 2024 amendment and false of the 2025 one.</td>
              <td className="py-3 align-top">&ldquo;Rule 4(14), substituted by S.O. 2374(E), 20 June 2024&rdquo;</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p>Three questions. If a consultant, a vendor or a summary cannot answer all three, treat the claim as unverified and go and read the notification. It is a public PDF on the CPCB EPR portal.</p>

      <h2>The rules that will actually cost you money are the ones nobody quotes</h2>
      <p>While everyone argued about QR codes, two real obligations sat mostly unquoted.</p>
      <p>The first is recycled content. S.O. 2374(E), notified 20 June 2024, substituted the table at Rule 4, sub-rule (14). It sets a minimum share of recycled material by dry weight in new batteries, by battery type, starting in FY 2027-28. That is eighteen months away. Five separate summaries referenced this table. Not one printed the numbers in it.</p>
      <p>The second is material recovery. The minimum a registered recycler must recover rises to 90% for EV and portable batteries in 2026-27. If your take-back partner is recovering less than that next year, your chain of custody has a hole in it, and the liability does not move to them. Under the 2022 rules, EPR liability on a battery you put into the market is perpetual.</p>
      <p>Perpetual is the word that matters. It does not end when you sell the pack. It does not end when the pack fails. It ends when a CPCB-registered recycler or refurbisher processes it and the certificate lands against your account.</p>
      <p>So the question for an OEM is not &ldquo;have I registered on the portal&rdquo;. It is &ldquo;can I prove where any given pack went&rdquo;.</p>

      <h2>What a lender should take from this</h2>
      <p>If you finance batteries, this is not somebody else&rsquo;s compliance problem.</p>
      <p>A pack&rsquo;s end-of-life route sets its residual value. Residual value sets your loss-given-default. If the OEM behind the asset cannot show a chain of custody, then the recovery number in your model is an assumption, not a projection.</p>
      <p>Ask the OEM the three questions above. Their answer tells you how carefully they read anything.</p>

      <h2>Where we sit in this</h2>
      <p>iTarang manages lithium packs across six stages: finance, deploy, monitor, maintain, buyback, recycle. There is an IoT device on every battery, and that is what makes the last two stages real rather than promised. The same health data that underwrites the loan sets the buyback price and decides whether a pack goes to second life or to a registered recycler. Chain of custody is not a document we produce at audit time. It is a by-product of running the loop. Most companies in this market own one stage and hand the pack to a stranger at the edge of it.</p>
      <p>The Battery Waste Management Rules 2022 will keep being amended, and the summaries will keep drifting from the notifications. The three questions travel better than any explainer, including this one.</p>
      <p><strong>If you make or import battery packs:</strong> send us your current take-back arrangement and the recovery percentage your recycler is contracted to. We will tell you whether it clears the 2026-27 threshold, and where the gap is if it does not.</p>
    </BlogLayout>
  );
}
