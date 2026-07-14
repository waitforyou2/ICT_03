# SpecDiff 审计结果

- 状态：`complete`
- 代码仓：`E:\code\ICT-master\ICT-master\challenges\03_ai_implementation_design_difference_detection\code\f-stack`
- 设计文档：`E:\code\ICT-master\ICT-master\challenges\03_ai_implementation_design_difference_detection\Difference\benchmark.md`
- 源文件：14457
- 规范条目：1287
- 已确认差异：6
- CodeGraph：`indexed (1.4.1); explore 6/6`

## 运行告警

- source skipped: dpdk\drivers\net\bnxt\hsi_struct_def_dpdk.h
- source skipped: freebsd\contrib\dev\ath\ath_hal\ar9300\osprey_reg_map_macro.h
- source skipped: freebsd\contrib\dev\ath\ath_hal\ar9300\scorpion_reg_map_macro.h
- source skipped: freebsd\contrib\libsodium\test\default\sign.c

## 1. IPv6 分片头查找未遍历扩展头链

- ID：`finding-41d4e76484e3`
- 分类：`normative_contradiction`；严重度：`high`；置信度：99%
- 标签：`ipv6-fragment-chain`, `self-admission`
- 适用条件：仅在该注释仍描述当前实现且仓库中不存在补偿实现时成立。

### 规范证据

> At the destination node, normal demultiplexing on the Next Header field of the IPv6 header invokes the module to process the first extension header, or the upper-layer header if no extension header is present. The contents and semantics of each extension header determine whether or not to proceed to the next header. Therefore, extension headers must be processed strictly in the order they appear in the packet; a receiver must not, for example, scan through a packet looking for a particular kind of extension header and process that header prior to processing all preceding ones.

来源：`RFC 8200` §4，`E:\code\ICT-master\ICT-master\challenges\03_ai_implementation_design_difference_detection\submission\work\specdiff\cache\rfc8200.txt:463`；强度 `must_not`。

### 实现行为

代码注释明确声明：only looks at the extension header that's right after the fixed IPv6 * header, and doesn't follow the whole chain

### 代码证据

- `dpdk/lib/ip_frag/rte_ip_frag.h:130`，符号 `rte_ipv6_frag_get_ipv6_fragment_header`：限制说明及只检查紧邻分片头的函数体

```text
130:
131:/**
132: * Return a pointer to the packet's fragment header, if found.
133: * It only looks at the extension header that's right after the fixed IPv6
134: * header, and doesn't follow the whole chain of extension headers.
135: *
136: * @param hdr
137: *   Pointer to the IPv6 header.
138: * @return
139: *   Pointer to the IPv6 fragment extension header, or NULL if it's not
140: *   present.
141: */
142:static inline struct rte_ipv6_fragment_ext *
143:rte_ipv6_frag_get_ipv6_fragment_header(struct rte_ipv6_hdr *hdr)
144:{
145:	if (hdr->proto == IPPROTO_FRAGMENT) {
146:		return (struct rte_ipv6_fragment_ext *) ++hdr;
147:	}
148:	else
149:		return NULL;
150:}
151:
```

### 证据链与反证

1. 发现实现自述限制
1. 定位限制对应代码区域
1. 与规范行为进行语义对齐

- 已检查：在全仓检索同主题实现词和替代路径，由证据门禁二次过滤
- 已检查：函数体仅判断固定 IPv6 头的 proto，未见扩展头链迭代
- 已检查：CodeGraph explore 调用图与影响面未发现足以推翻该结论的替代路径

## 2. Proxy 邻居通告缺少随机延迟

- ID：`finding-583cab8ac9c4`
- 分类：`normative_contradiction`；严重度：`medium`；置信度：98%
- 标签：`proxy-random-delay`, `self-admission`
- 适用条件：仅在该注释仍描述当前实现且仓库中不存在补偿实现时成立。

### 规范证据

> Finally, when sending a proxy advertisement in response to a Neighbor Solicitation, the sender should delay its response by a random time between 0 and MAX_ANYCAST_DELAY_TIME seconds to avoid collisions due to multiple responses sent by several proxies. However, in some cases (e.g., Mobile IPv6) where only one proxy is present, such delay is not necessary.

来源：`RFC 4861` §7.2.8，`E:\code\ICT-master\ICT-master\challenges\03_ai_implementation_design_difference_detection\submission\work\specdiff\cache\rfc4861.txt:3853`；强度 `recommendation`。

### 实现行为

代码注释明确声明：proxy advertisement delay rule (RFC2461 7.2.8, last paragraph, SHOULD)

### 代码证据

- `freebsd/netinet6/nd6_nbr.c:333`，符号 `nd6_ns_input`：NS 响应路径直接调用 NA 输出

```text
333:		struct in6_addr in6_all;
334:
335:		in6_all = in6addr_linklocal_allnodes;
336:		if (in6_setscope(&in6_all, ifp, NULL) != 0)
337:			goto bad;
338:		nd6_na_output_fib(ifp, &in6_all, &taddr6,
339:		    ((anycast || proxy || !tlladdr) ? 0 : ND_NA_FLAG_OVERRIDE) |
340:		    rflag, tlladdr, proxy ? (struct sockaddr *)&proxydl : NULL,
341:		    M_GETFIB(m));
342:		goto freeit;
343:	}
```

- `freebsd/netinet6/nd6_nbr.c:343`，符号 `nd6_ns_input`：NS 响应路径直接调用 NA 输出

```text
343:	}
344:
345:	nd6_cache_lladdr(ifp, &saddr6, lladdr, lladdrlen,
346:	    ND_NEIGHBOR_SOLICIT, 0);
347:
348:	nd6_na_output_fib(ifp, &saddr6, &taddr6,
349:	    ((anycast || proxy || !tlladdr) ? 0 : ND_NA_FLAG_OVERRIDE) |
350:	    rflag | ND_NA_FLAG_SOLICITED, tlladdr,
351:	    proxy ? (struct sockaddr *)&proxydl : NULL, M_GETFIB(m));
352: freeit:
353:	if (ifa != NULL)
```

- `freebsd/netinet6/nd6_nbr.c:647`，符号 `nd6_ns_output`：实现自述的能力缺口

```text
647: * Based on RFC 2462 (duplicate address detection)
648: *
649: * the following items are not implemented yet:
650: * - proxy advertisement delay rule (RFC2461 7.2.8, last paragraph, SHOULD)
651: * - anycast advertisement delay rule (RFC2461 7.2.7, SHOULD)
652: */
653:void
654:nd6_na_input(struct mbuf *m, int off, int icmp6len)
655:{
656:	struct ifnet *ifp;
657:	struct ip6_hdr *ip6;
```

### 证据链与反证

1. 发现实现自述限制
1. 定位限制对应代码区域
1. 与规范行为进行语义对齐

- 已检查：在全仓检索同主题实现词和替代路径，由证据门禁二次过滤
- 已检查：枚举 nd6_na_output_fib 实际调用点 3 个
- 已检查：CodeGraph explore 调用图与影响面未发现足以推翻该结论的替代路径

## 3. 缺少有状态 DHCPv6 地址配置支持

- ID：`finding-c24e5161cb3f`
- 分类：`feature_gap`；严重度：`medium`；置信度：98%
- 标签：`dhcpv6-absent`, `self-admission`
- 适用条件：仅在该注释仍描述当前实现且仓库中不存在补偿实现时成立。

### 规范证据

> This document describes DHCP for IPv6 (DHCPv6), a client/server protocol that provides managed configuration of devices. The basic operation of DHCPv6 provides configuration for clients connected to the same link as the server. Relay agent functionality is also defined for enabling communication between clients and servers that are not on the same link.

来源：`RFC 8415` §1，`E:\code\ICT-master\ICT-master\challenges\03_ai_implementation_design_difference_detection\submission\work\specdiff\cache\rfc8415.txt:320`；强度 `informative`。

### 实现行为

代码注释明确声明：do not support stateful * address configuration by DHCPv6

### 代码证据

- `freebsd/netinet6/icmp6.c:1837`，符号 `ni6_store_addrs`：实现自述的能力缺口

```text
1837:			 *    which the address was derived through Stateless
1838:			 *    Autoconfiguration.
1839:			 *
1840:			 * Note that we currently do not support stateful
1841:			 * address configuration by DHCPv6, so the former
1842:			 * case can't happen.
1843:			 */
1844:			if (ifa6->ia6_lifetime.ia6t_expire == 0)
1845:				ltime = ND6_INFINITE_LIFETIME;
1846:			else {
1847:				if (ifa6->ia6_lifetime.ia6t_expire >
```

### 证据链与反证

1. 发现实现自述限制
1. 定位限制对应代码区域
1. 与规范行为进行语义对齐

- 已检查：在全仓检索同主题实现词和替代路径，由证据门禁二次过滤
- 已检查：检索 DHCPv6、UDP 546/547、SOLICIT/REQUEST 与客户端处理路径
- 已检查：CodeGraph explore 调用图与影响面未发现足以推翻该结论的替代路径

## 4. 宽泛组播分支抢先返回，遮蔽后续 IPv6/MLD 分类

- ID：`finding-6118ff644d30`
- 分类：`functional_misrouting`；严重度：`high`；置信度：97%
- 标签：`mld-misrouting`, `control-flow`
- 适用条件：当特定协议报文同时满足前面的宽泛条件时触发。

### 规范证据

> Multicast Listener Query (Type = decimal 130)

来源：`RFC 2710` §3.1，`E:\code\ICT-master\ICT-master\challenges\03_ai_implementation_design_difference_detection\submission\work\specdiff\cache\rfc2710.txt:125`；强度 `informative`。

### 实现行为

宽泛的二层组播判断先返回，导致后面的 IPv6 细分逻辑不可达；NDP 类型范围也不包含 MLD 130–132。

### 代码证据

- `lib/ff_dpdk_if.c:1565`，符号 `protocol_filter`：先执行的宽泛组播分支

```text
1565:    }
1566:
1567:    /* Multicast protocol, such as stp(used by zebra), is forwarded to kni and has a separate speed limit */
1568:    if (rte_is_multicast_ether_addr(&hdr->dst_addr)) {
1569:        return FILTER_MULTI;
1570:    }
1571:
1572:#if (!defined(__FreeBSD__) && defined(INET6) ) || \
1573:    ( defined(__FreeBSD__) && defined(INET6) && defined(FF_KNI))
```

- `lib/ff_dpdk_if.c:1572`，符号 `protocol_filter`：被遮蔽的 IPv6 特定分支

```text
1572:#if (!defined(__FreeBSD__) && defined(INET6) ) || \
1573:    ( defined(__FreeBSD__) && defined(INET6) && defined(FF_KNI))
1574:    if (ether_type == RTE_ETHER_TYPE_IPV6) {
1575:        return ff_kni_proto_filter(data,
1576:            len, ether_type);
1577:    }
1578:#endif
1579:
```

- `lib/ff_dpdk_kni.c:287`，符号 `protocol_filter_icmp6`：后续分类仅覆盖 NDP 类型范围

```text
287:    const struct icmp6_hdr *hdr;
288:    hdr = (const struct icmp6_hdr *)data;
289:
290:    if (hdr->icmp6_type >= ND_ROUTER_SOLICIT && hdr->icmp6_type <= ND_REDIRECT)
291:        return FILTER_NDP;
292:
293:    return FILTER_UNKNOWN;
294:}
```

### 证据链与反证

1. 确认宽泛条件
1. 确认分支内提前返回
1. 确认特定协议判断位于其后
1. 核对消息类型覆盖范围

- 已检查：比较同一函数内两个条件的源代码顺序
- 已检查：确认前一分支含 return
- 已检查：CodeGraph explore 调用图与影响面未发现足以推翻该结论的替代路径

## 5. 固定上限 nd6_maxndopt=10 会提前终止集合处理

- ID：`finding-9139b7ab6bf4`
- 分类：`normative_contradiction`；严重度：`high`；置信度：94%
- 标签：`nd-option-limit`, `bounded-loop`
- 适用条件：当输入集合允许超过该实现上限且规范要求处理全部有效元素时触发。

### 规范证据

> After extracting information from the fixed part of the Router Advertisement message, the advertisement is scanned for valid options. If the advertisement contains a Source Link-Layer Address option, the link-layer address SHOULD be recorded in the Neighbor Cache entry for the router (creating an entry if necessary) and the IsRouter flag in the Neighbor Cache entry MUST be set to TRUE. If no Source Link-Layer Address is included, but a corresponding Neighbor Cache entry exists, its IsRouter flag MUST be set to TRUE. The IsRouter flag is used by Neighbor Unreachability Detection to determine when a router changes to being a host (i.e., no longer capable of forwarding packets). If a Neighbor Cache entry is created for the router, its reachability state MUST be set to STALE as specified in Section 7.3.3. If a cache entry already exists and is updated with a different link-layer address, the reachability state MUST also be set to STALE.

来源：`RFC 4861` §6.3.4，`E:\code\ICT-master\ICT-master\challenges\03_ai_implementation_design_difference_detection\submission\work\specdiff\cache\rfc4861.txt:3052`；强度 `must`。

### 实现行为

实现将 nd6_maxndopt 固定为 10，达到上限后通过 break/return 停止继续处理。

### 代码证据

- `freebsd/netinet6/nd6.c:118`，符号 `<file-scope>`：固定上限定义

```text
118:VNET_DEFINE_STATIC(int, nd6_gctimer) = (60 * 60 * 24); /* 1 day: garbage
119:							* collection timer */
120:#define	V_nd6_gctimer	VNET(nd6_gctimer)
121:
122:/* preventing too many loops in ND option parsing */
123:VNET_DEFINE_STATIC(int, nd6_maxndopt) = 10; /* max # of ND options allowed */
124:
```

- `freebsd/netinet6/nd6.c:521`，符号 `nd6_options`：上限触发提前退出

```text
521:skip1:
522:		i++;
523:		if (i > V_nd6_maxndopt) {
524:			ICMP6STAT_INC(icp6s_nd_toomanyopt);
525:			nd6log((LOG_INFO, "too many loop in nd opt\n"));
526:			break;
527:		}
528:
529:		if (ndopts->nd_opts_done)
530:			break;
531:	}
```

### 证据链与反证

1. 定位固定数值上限
1. 追踪上限在循环/条件中的使用
1. 确认存在提前退出路径

- 已检查：检索 nd6_maxndopt 的全部源码引用并确认存在退出语句
- 已检查：CodeGraph explore 调用图与影响面未发现足以推翻该结论的替代路径

## 6. 配置代理地址时未发送非请求式 Neighbor Advertisement

- ID：`finding-871a4c5273dd`
- 分类：`optional_capability_gap`；严重度：`low`；置信度：76%
- 标签：`proxy-unsolicited-na`, `optional-gap`
- 适用条件：这是 RFC 的 MAY 能力缺失，不等同于强制性违规。

### 规范证据

> A proxy MAY multicast Neighbor Advertisements when its link-layer address changes or when it is configured (by system management or other mechanisms) to proxy for an address. If there are multiple nodes that are providing proxy services for the same set of addresses, the proxies should provide a mechanism that prevents multiple proxies from multicasting advertisements for any one address, in order to reduce the risk of excessive multicast traffic. This is a requirement on other protocols that need to use proxies for Neighbor Advertisements. An example of a node that performs proxy advertisements is the Home Agent specified in [MIPv6].

来源：`RFC 4861` §7.2.6，`E:\code\ICT-master\ICT-master\challenges\03_ai_implementation_design_difference_detection\submission\work\specdiff\cache\rfc4861.txt:3775`；强度 `may`。

### 实现行为

NA 输出调用仅出现在 Neighbor Solicitation 响应路径；未发现代理地址配置事件触发的非请求式 NA。

### 代码证据

- `freebsd/netinet6/nd6_nbr.c:333`，符号 `nd6_ns_input`：NA 输出调用点；上下文均为收到 NS 后响应

```text
333:		struct in6_addr in6_all;
334:
335:		in6_all = in6addr_linklocal_allnodes;
336:		if (in6_setscope(&in6_all, ifp, NULL) != 0)
337:			goto bad;
338:		nd6_na_output_fib(ifp, &in6_all, &taddr6,
339:		    ((anycast || proxy || !tlladdr) ? 0 : ND_NA_FLAG_OVERRIDE) |
340:		    rflag, tlladdr, proxy ? (struct sockaddr *)&proxydl : NULL,
341:		    M_GETFIB(m));
342:		goto freeit;
343:	}
```

- `freebsd/netinet6/nd6_nbr.c:343`，符号 `nd6_ns_input`：NA 输出调用点；上下文均为收到 NS 后响应

```text
343:	}
344:
345:	nd6_cache_lladdr(ifp, &saddr6, lladdr, lladdrlen,
346:	    ND_NEIGHBOR_SOLICIT, 0);
347:
348:	nd6_na_output_fib(ifp, &saddr6, &taddr6,
349:	    ((anycast || proxy || !tlladdr) ? 0 : ND_NA_FLAG_OVERRIDE) |
350:	    rflag | ND_NA_FLAG_SOLICITED, tlladdr,
351:	    proxy ? (struct sockaddr *)&proxydl : NULL, M_GETFIB(m));
352: freeit:
353:	if (ifa != NULL)
```

- `freebsd/netinet6/nd6_nbr.c:1129`，符号 `nd6_na_output`：NA 输出调用点；上下文均为收到 NS 后响应

```text
1129:nd6_na_output(struct ifnet *ifp, const struct in6_addr *daddr6_0,
1130:    const struct in6_addr *taddr6, u_long flags, int tlladdr,
1131:    struct sockaddr *sdl0)
1132:{
1133:
1134:	nd6_na_output_fib(ifp, daddr6_0, taddr6, flags, tlladdr, sdl0,
1135:	    RT_DEFAULT_FIB);
1136:}
1137:#endif
1138:
1139:caddr_t
```

### 证据链与反证

1. 从 MAY 规范抽取配置事件与发送动作
1. 枚举 NA 输出调用点
1. 反向检查配置路径
1. 确认覆盖缺口

- 已检查：枚举 nd6_na_output_fib 调用点 3 个
- 已检查：未发现 config/proxy-add/route-add 上下文调用
- 已检查：CodeGraph explore 调用图与影响面未发现足以推翻该结论的替代路径
