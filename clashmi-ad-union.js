// Clash Mi 本地广告覆写：保留原订阅节点和分流，每次加载配置时前置广告规则。
// 合并广告库每六小时更新；命中奖励广告时，领取金币/权益可能失败。
// 回滚：将该订阅的“核心覆写”切回原来的设置。
function main(config) {
  if (!config || typeof config !== "object" || !Array.isArray(config.rules)) {
    throw new Error("原订阅不是包含 rules 的 Clash 配置，已停止覆写");
  }
  const originalRules = config.rules.slice();
  const groups = Array.isArray(config["proxy-groups"]) ? config["proxy-groups"] : [];
  let adGroup = "广告过滤（本地）";
  while (groups.some(function (group) { return group.name === adGroup; })) {
    adGroup += "+";
  }
  config["proxy-groups"] = groups.concat([{name: adGroup, type: "select", proxies: ["REJECT", "DIRECT"]}]);
  const providers = Object.assign({}, config["rule-providers"] || {});
  let unionName = "zing-ad-union";
  while (Object.prototype.hasOwnProperty.call(providers, unionName)) unionName += "-local";
  providers[unionName] = {
    type: "http", behavior: "domain", format: "mrs",
    url: "https://github.com/ZingYao/clash-ad-rules/releases/latest/download/ads.mrs",
    path: "./ruleset/zing-ad-union.mrs", interval: 21600
  };
  config["rule-providers"] = providers;
  const hongguoDomains = [
    "api-access.pangolin-sdk-toutiao.com",
    "api-access.pangolin-sdk-toutiao1.com",
    "api-access.pangolin-sdk-toutiao-b.com",
    "gromore.pangolin-sdk-toutiao.com",
    "ether-pack.pangolin-sdk-toutiao.com",
    "sf3-fe-tos.pglstatp-toutiao.com",
    "sf6-fe-tos.pglstatp-toutiao.com"
  ];
  const adRules = hongguoDomains.map(function (domain) { return "DOMAIN," + domain + "," + adGroup; });
  adRules.push("RULE-SET," + unionName + "," + adGroup);
  // 完全相同的路由仅保留第一条，保持首次匹配顺序。
  const seenRules = new Set();
  config.rules = adRules.concat(originalRules).filter(function (rule) {
    if (seenRules.has(rule)) return false;
    seenRules.add(rule);
    return true;
  });
  // 从握手信息识别直接访问 IP 的连接，不解密 HTTPS，也不替换目标地址。
  const originalSniffer = config.sniffer || {};
  const sniffProtocols = Object.assign({}, originalSniffer.sniff || {});
  sniffProtocols.HTTP = Object.assign({}, sniffProtocols.HTTP || {}, {ports: [80, "8080-8880"], "override-destination": false});
  sniffProtocols.TLS = Object.assign({}, sniffProtocols.TLS || {}, {ports: [443, 4430, 8443], "override-destination": false});
  sniffProtocols.QUIC = Object.assign({}, sniffProtocols.QUIC || {}, {ports: [443, 4430, 8443], "override-destination": false});
  config.sniffer = Object.assign({}, originalSniffer, {
    enable: true, "force-dns-mapping": true, "parse-pure-ip": true,
    "override-destination": false, sniff: sniffProtocols
  });
  config.mode = "rule";
  return JSON.stringify(config);
}
