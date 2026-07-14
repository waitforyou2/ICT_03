# CodeGraph graph evidence

## finding-41d4e76484e3 — IPv6 分片头查找未遍历扩展头链

Query: `Trace the implementation and all relevant callers for IPv6 分片头查找未遍历扩展头链. Start from dpdk/lib/ip_frag/rte_ip_frag.h symbol rte_ipv6_frag_get_ipv6_fragment_header. Look specifically for an alternative implementation or counterevidence that would make the suspected design-to-code difference invalid.`

**Dynamic-dispatch links among your symbols**
(synthesized — the indirect hops grep/Read would reconstruct; the `@file:line` is the wiring site)

- ng_generic_msg → ngs_rcvmsg   [dynamic: fn-pointer ng_type.rcvmsg @freebsd/netgraph/ng_base.c:2934]

> Full source for these symbols is below — the call flow among them, followed by their bodies.
**Exploration: Trace the implementation and all relevant callers for IPv6 分片头查找未遍历扩展头链. Start from dpdk/lib/ip_frag/rte_ip_frag.h symbol rte_ipv6_frag_get_ipv6_fragment_header. Look specifically for an alternative implementation or counterevidence that would make the suspected design-to-code difference invalid.**

Found 15 symbols across 6 files.

**Blast radius — what depends on these (update/verify before editing)**

- `rte_ipv6_frag_get_ipv6_fragment_header` (dpdk/lib/ip_frag/rte_ip_frag.h:142) — 3 callers in `dpdk/lib/port/rte_port_ras.c`; tests: `dpdk/examples/ipsec-secgw/ipsec-secgw.c`, `dpdk/examples/ip_reassembly/main.c`

**Relationships**

**calls:**
- rx_callback → rte_ipv6_frag_get_ipv6_fragment_header
- reassemble → rte_ipv6_frag_get_ipv6_fragment_header
- process_ipv6 → rte_ipv6_frag_get_ipv6_fragment_header
- rx_callback → rte_ipv4_frag_pkt_is_fragmented
- rx_callback → rte_rdtsc
- rx_callback → rte_ipv4_frag_reassemble_packet
- rx_callback → rte_ipv4_cksum
- rx_callback → rte_ipv6_frag_reassemble_packet
- rx_callback → rte_ip_frag_free_death_row
- reassemble → rte_ipv4_frag_pkt_is_fragmented
- reassemble → rte_ipv4_frag_reassemble_packet
- reassemble → rte_lpm_lookup
- reassemble → rte_ipv6_frag_reassemble_packet
- reassemble → rte_lpm6_lookup
- reassemble → rte_ether_addr_copy
- ... and 16 more

**references:**
- reassemble_lcore_init → rx_callback
- reassemble → ports_eth_addr
- reassemble → enabled_port_mask
- main_loop → enabled_port_mask

**Source Code**

> The code below is the **verbatim, current on-disk source** of these files — re-read from disk on this call and line-numbered, byte-for-byte identical to what the Read tool returns. It is NOT a summary, outline, or stale cache. Treat each block as a Read you have already performed: do not Read a file shown here.

**`dpdk/lib/ip_frag/rte_ip_frag.h`** — rte_ip_frag_death_row(struct), rte_ipv6_frag_get_ipv6_fragment_header(function), rte_ipv4_frag_pkt_is_fragmented(function)

```c
35		(RTE_IP_FRAG_DEATH_ROW_LEN * (RTE_LIBRTE_IP_FRAG_MAX_FRAG + 1))
36	
37	/** mbuf death row (packets to be freed) */
38	struct rte_ip_frag_death_row {
39		uint32_t cnt;          /**< number of mbufs currently on death row */
40		struct rte_mbuf *row[RTE_IP_FRAG_DEATH_ROW_MBUF_LEN];
41		/**< mbufs to be freed */
42	};
43	
44	/**
45	 * Create a new IP fragmentation table.

... (gap) ...

139	 *   Pointer to the IPv6 fragment extension header, or NULL if it's not
140	 *   present.
141	 */
142	static inline struct rte_ipv6_fragment_ext *
143	rte_ipv6_frag_get_ipv6_fragment_header(struct rte_ipv6_hdr *hdr)
144	{
145		if (hdr->proto == IPPROTO_FRAGMENT) {
146			return (struct rte_ipv6_fragment_ext *) ++hdr;
147		}
148		else
149			return NULL;
150	}
151	
152	/**
153	 * IPv4 fragmentation.

... (gap) ...

242	 * @return
243	 *   1 if fragmented, 0 if not fragmented
244	 */
245	static inline int
246	rte_ipv4_frag_pkt_is_fragmented(const struct rte_ipv4_hdr *hdr)
247	{
248		uint16_t flag_offset, ip_flag, ip_ofs;
249	
250		flag_offset = rte_be_to_cpu_16(hdr->fragment_offset);
251		ip_ofs = (uint16_t)(flag_offset & RTE_IPV4_HDR_OFFSET_MASK);
252		ip_flag = (uint16_t)(flag_offset & RTE_IPV4_HDR_MF_FLAG);
253	
254		return ip_flag != 0 || ip_ofs  != 0;
255	}
256	
257	/**
258	 * Free mbufs on a given death row.
```

**`dpdk/lib/ip_frag/ip_reassembly.h`** — ip_frag(struct), rte_ip_frag_tbl(struct), ip_frag_key(struct), <anonymous>(struct)

```c
1	/* SPDX-License-Identifier: BSD-3-Clause
2	 * Copyright(c) 2010-2021 Intel Corporation
3	 */
4	
5	#ifndef _IP_REASSEMBLY_H_
6	#define _IP_REASSEMBLY_H_
7	
8	/*
9	 * IP Fragmentation and Reassembly
10	 * Implementation of IP packet fragmentation and reassembly.
11	 */
12	
13	#include <rte_ip_frag.h>
14	
15	enum {
16		IP_LAST_FRAG_IDX,    /* index of last fragment */
17		IP_FIRST_FRAG_IDX,   /* index of first fragment */
18		IP_MIN_FRAG_NUM,     /* minimum number of fragments */
19		IP_MAX_FRAG_NUM = RTE_LIBRTE_IP_FRAG_MAX_FRAG,
20		/* maximum number of fragments per packet */
21	};
22	
23	/* fragmented mbuf */
24	struct ip_frag {
25		uint16_t ofs;        /* offset into the packet */
26		uint16_t len;        /* length of fragment */
27		struct rte_mbuf *mb; /* fragment mbuf */
28	};
29	
30	/*
31	 * key: <src addr, dst_addr, id> to uniquely identify fragmented datagram.
32	 */
33	struct ip_frag_key {
34		uint64_t src_dst[4];
35		/* src and dst address, only first 8 bytes used for IPv4 */
36		union {
37			uint64_t id_key_len; /* combined for easy fetch */
38			__extension__
39			struct {
40				uint32_t id;      /* packet id */
41				uint32_t key_len; /* src/dst key length */
42			};
43		};
44	};
45	
46	/*
47	 * Fragmented packet to reassemble.
48	 * First two entries in the frags[] array are for the last and first fragments.
49	 */
50	struct __rte_cache_aligned ip_frag_pkt {
51		RTE_TAILQ_ENTRY(ip_frag_pkt) lru;      /* LRU list */
52		struct ip_frag_key key;                /* fragmentation key */
53		uint64_t start;                        /* creation timestamp */
54		uint32_t total_size;                   /* expected reassembled size */
55		uint32_t frag_size;                    /* size of fragments received */
56		uint32_t last_idx;                     /* index of next entry to fill */
57		struct ip_frag frags[IP_MAX_FRAG_NUM]; /* fragments */
58	};
59	
60	 /* fragments tailq */
61	RTE_TAILQ_HEAD(ip_pkt_list, ip_frag_pkt);
62	
63	/* fragmentation table statistics */
64	struct __rte_cache_aligned ip_frag_tbl_stat {
65		uint64_t find_num;     /* total # of find/insert attempts. */
66		uint64_t add_num;      /* # of add ops. */
67		uint64_t del_num;      /* # of del ops. */
68		uint64_t reuse_num;    /* # of reuse (del/add) ops. */
69		uint64_t fail_total;   /* total # of add failures. */
70		uint64_t fail_nospace; /* # of 'no space' add failures. */
71	};
72	
73	/* fragmentation table */
74	struct rte_ip_frag_tbl {
75		uint64_t max_cycles;     /* ttl for table entries. */
76		uint32_t entry_mask;     /* hash value mask. */
77		uint32_t max_entries;    /* max entries allowed. */
78		uint32_t use_entries;    /* entries in use. */
79		uint32_t bucket_entries; /* hash associativity. */
80		uint32_t nb_entries;     /* total size of the table. */
81		uint32_t nb_buckets;     /* num of associativity lines. */
82		struct ip_frag_pkt *last;     /* last used entry. */
83		struct ip_pkt_list lru;       /* LRU list for table entries. */
84		struct ip_frag_tbl_stat stat; /* statistics counters. */
85		struct ip_frag_pkt pkt[]; /* hash table. */
86	};
87	
88	#endif /* _IP_REASSEMBLY_H_ */
```

**`dpdk/lib/eal/common/eal_trace.h`** — trace(struct)

```c
1	/* SPDX-License-Identifier: BSD-3-Clause
2	 * Copyright(C) 2020 Marvell International Ltd.
3	 */
4	
5	#ifndef __EAL_TRACE_H
6	#define __EAL_TRACE_H
7	
8	#include <rte_cycles.h>
9	#include <rte_log.h>
10	#include <rte_malloc.h>
11	#include <rte_spinlock.h>
12	#include <rte_trace.h>
13	#include <rte_trace_point.h>
14	#include <rte_uuid.h>
15	
16	#include "eal_private.h"
17	#include "eal_thread.h"
18	
19	#define trace_err(...) \
20		RTE_LOG_LINE_PREFIX(ERR, EAL, "%s():%u ", __func__ RTE_LOG_COMMA __LINE__, __VA_ARGS__)
21	
22	#define trace_crit(...) \
23		RTE_LOG_LINE_PREFIX(CRIT, EAL, "%s():%u ", __func__ RTE_LOG_COMMA __LINE__, __VA_ARGS__)
24	
25	#define TRACE_CTF_MAGIC 0xC1FC1FC1
26	#define TRACE_MAX_ARGS	32
27	
28	struct trace_point {
29		STAILQ_ENTRY(trace_point) next;
30		rte_trace_point_t *handle;
31		const char *name;
32		char *ctf_field;
33	};
34	
35	enum trace_area_e {
36		TRACE_AREA_HEAP,
37		TRACE_AREA_HUGEPAGE,
38	};
39	
40	struct thread_mem_meta {
41		void *mem;
42		enum trace_area_e area;
43	};
44	
45	struct trace_arg {
46		STAILQ_ENTRY(trace_arg) next;
47		char *val;
48	};
49	
50	struct trace {
51		char *dir;
52		int register_errno;
53		RTE_ATOMIC(uint32_t) status;
54		enum rte_trace_mode mode;
55		rte_uuid_t uuid;
56		uint32_t buff_len;
57		STAILQ_HEAD(, trace_arg) args;
58		uint32_t nb_trace_points;
59		uint32_t nb_trace_mem_list;
60		struct thread_mem_meta *lcore_meta;
61		uint64_t epoch_sec;
62		uint64_t epoch_nsec;
63		uint64_t uptime_ticks;
64		char *ctf_meta;
65		uint32_t ctf_meta_offset_freq;
66		uint32_t ctf_meta_offset_freq_off_s;
67		uint32_t ctf_meta_offset_freq_off;
68		RTE_ATOMIC(uint16_t) ctf_fixup_done;
69		rte_spinlock_t lock;
70	};
71	
72	/* Helper functions */
73	static inline uint16_t
74	trace_id_get(rte_trace_point_t *trace)
75	{
76		return (*trace & __RTE_TRACE_FIELD_ID_MASK) >>
77			__RTE_TRACE_FIELD_ID_SHIFT;
78	}
79	
80	static inline size_t
81	trace_mem_sz(uint32_t len)
82	{
83		return len + sizeof(struct __rte_trace_header);
84	}
85	
86	/* Trace object functions */
87	struct trace *trace_obj_get(void);
88	
89	/* Trace point list functions */
90	STAILQ_HEAD(trace_point_head, trace_point);
91	struct trace_point_head *trace_list_head_get(void);
92	
93	/* Util functions */
94	const char *trace_mode_to_string(enum rte_trace_mode mode);
95	const char *trace_area_to_string(enum trace_area_e area);
96	int trace_args_apply(const char *arg);
97	void trace_bufsz_args_apply(void);
98	bool trace_has_duplicate_entry(void);
99	void trace_uuid_generate(void);
100	int trace_metadata_create(void);
101	void trace_metadata_destroy(void);
102	char *trace_metadata_fixup_field(const char *field);
103	int trace_epoch_time_save(void);
104	void trace_mem_free(void);
105	void trace_mem_per_thread_free(void);
106	
107	/* EAL interface */
108	int eal_trace_init(void);
109	void eal_trace_fini(void);
110	int eal_trace_args_save(const char *val);
111	void eal_trace_args_free(void);
112	int eal_trace_dir_args_save(const char *val);
113	int eal_trace_mode_args_save(const char *val);
114	int eal_trace_bufsz_args_save(const char *val);
115	
116	#endif /* __EAL_TRACE_H */
```

**`dpdk/lib/eal/common/eal_common_trace.c`** — trace(variable)

```c
21	static RTE_DEFINE_PER_LCORE(char *, ctf_field);
22	
23	static struct trace_point_head tp_list = STAILQ_HEAD_INITIALIZER(tp_list);
24	static struct trace trace = { .args = STAILQ_HEAD_INITIALIZER(trace.args), };
25	
26	struct trace *
27	trace_obj_get(void)
```

**`dpdk/lib/pipeline/rte_swx_pipeline_internal.h`** — header(struct)

```c
219	/*
220	 * Header.
221	 */
222	struct header {
223		TAILQ_ENTRY(header) node;
224		char name[RTE_SWX_NAME_SIZE];
225		struct struct_type *st;
226		uint32_t struct_id;
227		uint32_t id;
228	};
229	
230	TAILQ_HEAD(header_tailq, header);
231	
```

**`dpdk/examples/ip_reassembly/main.c`** — calls(calls), reassemble(calls), enabled_port_mask(variable), send_single_packet(function), reassemble(function), rte_ipv4_frag_pkt_is_fragmented(calls), rte_ipv4_frag_reassemble_packet(calls), rte_lpm_lookup(calls), rte_ipv6_frag_get_ipv6_fragment_header(calls), rte_ipv6_frag_reassemble_packet(calls), rte_lpm6_lookup(calls), rte_ether_addr_copy(calls), send_single_packet(calls), main_loop(function), rte_rdtsc(calls), +1 more

```c
118	#define IPV6_ADDR_LEN 16
119	
120	/* mask of enabled ports */
121	static uint32_t enabled_port_mask = 0;
122	
123	static int rx_queue_per_lcore = 1;
124	

... (gap) ...

275	}
276	
277	/* Enqueue a single packet, and send burst if queue is filled */
278	static inline int
279	send_single_packet(struct rte_mbuf *m, uint16_t port)
280	{
281		uint32_t fill, lcore_id, len;
282		struct lcore_queue_conf *qconf;
283		struct mbuf_table *txmb;
284	
285		lcore_id = rte_lcore_id();
286		qconf = &lcore_queue_conf[lcore_id];
287	
288		txmb = qconf->tx_mbufs[port];
289		len = txmb->len;
290	
291		fill = send_burst(qconf, MAX_PKT_BURST, port);
292	
293		if (fill == len - 1) {
294			TX_LCORE_STAT_UPDATE(&qconf->tx_stat, drop, 1);
295			rte_pktmbuf_free(txmb->m_table[txmb->tail]);
296			if (++txmb->tail == len)
297				txmb->tail = 0;
298		}
299	
300		TX_LCORE_STAT_UPDATE(&qconf->tx_stat, queue, 1);
301		txmb->m_table[txmb->head] = m;
302		if(++txmb->head == len)
303			txmb->head = 0;
304	
305		return 0;
306	}
307	
308	static inline void
309	reassemble(struct rte_mbuf *m, uint16_t portid, uint32_t queue,
310		struct lcore_queue_conf *qconf, uint64_t tms)
311	{
312		struct rte_ether_hdr *eth_hdr;
313		struct rte_ip_frag_tbl *tbl;
314		struct rte_ip_frag_death_row *dr;
315		struct rx_queue *rxq;
316		void *d_addr_bytes;
317		uint32_t next_hop;
318		uint16_t dst_port;
319	
320		rxq = &qconf->rx_queue_list[queue];
321	
322		eth_hdr = rte_pktmbuf_mtod(m, struct rte_ether_hdr *);
323	
324		dst_port = portid;
325	
326		/* if packet is IPv4 */
327		if (RTE_ETH_IS_IPV4_HDR(m->packet_type)) {
328			struct rte_ipv4_hdr *ip_hdr;
329			uint32_t ip_dst;
330	
331			ip_hdr = (struct rte_ipv4_hdr *)(eth_hdr + 1);
332	
333			 /* if it is a fragmented packet, then try to reassemble. */
334			if (rte_ipv4_frag_pkt_is_fragmented(ip_hdr)) {
335				struct rte_mbuf *mo;
336	
337				tbl = rxq->frag_tbl;
338				dr = &qconf->death_row;
339	
340				/* prepare mbuf: setup l2_len/l3_len. */
341				m->l2_len = sizeof(*eth_hdr);
342				m->l3_len = sizeof(*ip_hdr);
343	
344				/* process this fragment. */
345				mo = rte_ipv4_frag_reassemble_packet(tbl, dr, m, tms, ip_hdr);
346				if (mo == NULL)
347					/* no packet to send out. */
348					return;
349	
350				/* we have our packet reassembled. */
351				if (mo != m) {
352					m = mo;
353					eth_hdr = rte_pktmbuf_mtod(m,
354						struct rte_ether_hdr *);
355					ip_hdr = (struct rte_ipv4_hdr *)(eth_hdr + 1);
356				}
357	
358				/* update offloading flags */
359				m->ol_flags |= (RTE_MBUF_F_TX_IPV4 | RTE_MBUF_F_TX_IP_CKSUM);
360			}
361			ip_dst = rte_be_to_cpu_32(ip_hdr->dst_addr);
362	
363			/* Find destination port */
364			if (rte_lpm_lookup(rxq->lpm, ip_dst, &next_hop) == 0 &&
365					(enabled_port_mask & 1 << next_hop) != 0) {
366				dst_port = next_hop;
367			}
368	
369			eth_hdr->ether_type = rte_be_to_cpu_16(RTE_ETHER_TYPE_IPV4);
370		} else if (RTE_ETH_IS_IPV6_HDR(m->packet_type)) {
371			/* if packet is IPv6 */
372			struct rte_ipv6_fragment_ext *frag_hdr;
373			struct rte_ipv6_hdr *ip_hdr;
374	
375			ip_hdr = (struct rte_ipv6_hdr *)(eth_hdr + 1);
376	
377			frag_hdr = rte_ipv6_frag_get_ipv6_fragment_header(ip_hdr);
378	
379			if (frag_hdr != NULL) {
380				struct rte_mbuf *mo;
381	
382				tbl = rxq->frag_tbl;
383				dr  = &qconf->death_row;
384	
385				/* prepare mbuf: setup l2_len/l3_len. */
386				m->l2_len = sizeof(*eth_hdr);
387				m->l3_len = sizeof(*ip_hdr) + sizeof(*frag_hdr);
388	
389				mo = rte_ipv6_frag_reassemble_packet(tbl, dr, m, tms, ip_hdr, frag_hdr);
390				if (mo == NULL)
391					return;
392	
393				if (mo != m) {
394					m = mo;
395					eth_hdr = rte_pktmbuf_mtod(m,
396								struct rte_ether_hdr *);
397					ip_hdr = (struct rte_ipv6_hdr *)(eth_hdr + 1);
398				}
399			}
400	
401			/* Find destination port */
402			if (rte_lpm6_lookup(rxq->lpm6, &ip_hdr->dst_addr,
403							&next_hop) == 0 &&
404					(enabled_port_mask & 1 << next_hop) != 0) {
405				dst_port = next_hop;
406			}
407	
408			eth_hdr->ether_type = rte_be_to_cpu_16(RTE_ETHER_TYPE_IPV6);
409		}
410		/* if packet wasn't IPv4 or IPv6, it's forwarded to the port it came from */
411	
412		/* 02:00:00:00:00:xx */
413		d_addr_bytes = &eth_hdr->dst_addr.addr_bytes[0];
414		*((uint64_t *)d_addr_bytes) = 0x000000000002 + ((uint64_t)dst_port << 40);
415	
416		/* src addr */
417		rte_ether_addr_copy(&ports_eth_addr[dst_port], &eth_hdr->src_addr);
418	
419		send_single_packet(m, dst_port);
420	}
421	
422	/* main processing loop */
423	static int
424	main_loop(__rte_unused void *dummy)
425	{
426		struct rte_mbuf *pkts_burst[MAX_PKT_BURST];
427		unsigned lcore_id;
428		uint64_t diff_tsc, cur_tsc, prev_tsc;
429		int i, j, nb_rx;
430		uint16_t portid;
431		struct lcore_queue_conf *qconf;
432		const uint64_t drain_tsc = (rte_get_tsc_hz() + US_PER_S - 1) / US_PER_S * BURST_TX_DRAIN_US;
433	
434		prev_tsc = 0;
435	
436		lcore_id = rte_lcore_id();
437		qconf = &lcore_queue_conf[lcore_id];
438	
439		if (qconf->n_rx_queue == 0) {
440			RTE_LOG(INFO, IP_RSMBL, "lcore %u has nothing to do\n", lcore_id);
441			return 0;
442		}
443	
444		RTE_LOG(INFO, IP_RSMBL, "entering main loop on lcore %u\n", lcore_id);
445	
446		for (i = 0; i < qconf->n_rx_queue; i++) {
447	
448			portid = qconf->rx_queue_list[i].portid;
449			RTE_LOG(INFO, IP_RSMBL, " -- lcoreid=%u portid=%u\n", lcore_id,
450				portid);
451		}
452	
453		while (1) {
454	
455			cur_tsc = rte_rdtsc();
456	
457			/*
458			 * TX burst queue drain
459			 */
460			diff_tsc = cur_tsc - prev_tsc;
461			if (unlikely(diff_tsc > drain_tsc)) {
462	
463				/*
464				 * This could be optimized (use queueid instead of
465				 * portid), but it is not called so often
466				 */
467				for (portid = 0; portid < RTE_MAX_ETHPORTS; portid++) {
468					if ((enabled_port_mask & (1 << portid)) != 0)
469						send_burst(qconf, 1, portid);
470				}
471	
472				prev_tsc = cur_tsc;
473			}
474	
475			/*
476			 * Read packet from RX queues
477			 */
478			for (i = 0; i < qconf->n_rx_queue; ++i) {
479	
480				portid = qconf->rx_queue_list[i].portid;
481	
482				nb_rx = rte_eth_rx_burst(portid, 0, pkts_burst,
483					MAX_PKT_BURST);
484	
485				/* Prefetch first packets */
486				for (j = 0; j < PREFETCH_OFFSET && j < nb_rx; j++) {
487					rte_prefetch0(rte_pktmbuf_mtod(
488							pkts_burst[j], void *));
489				}
490	
491				/* Prefetch and forward already prefetched packets */
492				for (j = 0; j < (nb_rx - PREFETCH_OFFSET); j++) {
493					rte_prefetch0(rte_pktmbuf_mtod(pkts_burst[
494						j + PREFETCH_OFFSET], void *));
495					reassemble(pkts_burst[j], portid,
496						i, qconf, cur_tsc);
497				}
498	
499				/* Forward remaining prefetched packets */
500				for (; j < nb_rx; j++) {
501					reassemble(pkts_burst[j], portid,
502						i, qconf, cur_tsc);
503				}
504	
505				rte_ip_frag_free_death_row(&qconf->death_row,
506					PREFETCH_OFFSET);
507			}
508		}
509	}
510	
511	/* display usage */
512	static void
```

**Not shown above — explore these names for their source**

- dpdk/lib/eal/loongarch/include/rte_cycles.h: rte_rdtsc:20
- dpdk/lib/ip_frag/rte_ipv4_reassembly.c: rte_ipv4_frag_reassemble_packet:97
- dpdk/lib/net/rte_ip4.h: rte_ipv4_cksum:158
- dpdk/lib/ip_frag/rte_ipv6_reassembly.c: rte_ipv6_frag_reassemble_packet:135
- dpdk/lib/ip_frag/rte_ip_frag_common.c: rte_ip_frag_free_death_row:17
- dpdk/lib/lpm/rte_lpm.h: rte_lpm_lookup:278
- dpdk/lib/lpm/rte_lpm6.c: rte_lpm6_lookup:911
- dpdk/lib/net/rte_ether.h: rte_ether_addr_copy:238
- dpdk/drivers/net/bonding/rte_eth_bond_pmd.c: burst_xmit_l34_hash:758
- dpdk/lib/node/ip4_reassembly.c: ip4_reassembly_node_process:42
- ... and 5 more files

---
> **Complete source for 6 files is included above — do NOT re-read them.** If your question also needs files/symbols listed under "Not shown above" (or any area this call didn't cover), make ANOTHER codegraph_explore targeting those names — it returns the same source with line numbers and is cheaper and more complete than reading. Reserve Read for a single specific line range explore can't surface.

> **Explore budget: 3 calls for this project (14,182 files indexed).** Each call covers ~6 files; if your question spans more, spend your remaining calls on the uncovered area BEFORE falling back to Read — another explore is cheaper and more complete than reading those files. Synthesize once you've used 3.

## finding-583cab8ac9c4 — Proxy 邻居通告缺少随机延迟

Query: `Trace the implementation and all relevant callers for Proxy 邻居通告缺少随机延迟. Start from freebsd/netinet6/nd6_nbr.c symbol nd6_ns_input. Look specifically for an alternative implementation or counterevidence that would make the suspected design-to-code difference invalid.`

**Dynamic-dispatch links among your symbols**
(synthesized — the indirect hops grep/Read would reconstruct; the `@file:line` is the wiring site)

- ng_generic_msg → ngs_rcvmsg   [dynamic: fn-pointer ng_type.rcvmsg @freebsd/netgraph/ng_base.c:2934]

> Full source for these symbols is below — the call flow among them, followed by their bodies.
**Exploration: Trace the implementation and all relevant callers for Proxy 邻居通告缺少随机延迟. Start from freebsd/netinet6/nd6_nbr.c symbol nd6_ns_input. Look specifically for an alternative implementation or counterevidence that would make the suspected design-to-code difference invalid.**

Found 5 symbols across 2 files.

**Blast radius — what depends on these (update/verify before editing)**

- `nd6_ns_input` (freebsd/netinet6/nd6_nbr.c:126) — 2 callers in `freebsd/netinet6/icmp6.c`, `freebsd/netinet6/send.c`; ⚠️ no covering tests found
- `make` (freebsd/contrib/libsodium/packaging/dotnet-core/prepare.py:67) — 1 caller in `freebsd/contrib/libsodium/packaging/dotnet-core/prepare.py`; ⚠️ no covering tests found

**Relationships**

**calls:**
- nd6_ns_input → ip6_sprintf
- nd6_ns_input → if_name
- nd6_ns_input → m_pullup
- nd6_ns_input → in6_setscope
- nd6_ns_input → nd6_is_addr_neighbor
- nd6_ns_input → nd6_option_init
- nd6_ns_input → nd6_options
- nd6_ns_input → in6ifa_ifpwithaddr
- nd6_ns_input → nd6_proxy_fill_sdl
- nd6_ns_input → nd6_dad_ns_input
- nd6_ns_input → nd6_na_output_fib
- nd6_ns_input → nd6_cache_lladdr
- nd6_ns_input → ifa_free
- nd6_ns_input → m_freem
- icmp6_input → nd6_ns_input
- ... and 33 more

**instantiates:**
- main → WindowsItem
- main → Version
- main → MacOSItem
- main → LinuxItem
- main → ExtraItem

**references:**
- main → MAKEFILE
- main → DOCKER
- main → PROPSFILE
- main → EXTRAS
- main → LINUX
- main → MACOS
- main → WINDOWS
- __init__ → LIBRARY
- __init__ → CACHEDIR
- __init__ → LIBRARY
- __init__ → CACHEDIR
- make → DOCKER
- __init__ → LIBRARY
- __init__ → CACHEDIR
- __init__ → CACHEDIR

**Source Code**

> The code below is the **verbatim, current on-disk source** of these files — re-read from disk on this call and line-numbered, byte-for-byte identical to what the Read tool returns. It is NOT a summary, outline, or stale cache. Treat each block as a Read you have already performed: do not Read a file shown here.

**`freebsd/contrib/libsodium/src/libsodium/randombytes/randombytes.c`** — implementation(constant)

```c
1	
2	#include <assert.h>
3	#include <limits.h>
4	#include <stdint.h>
5	#include <stdlib.h>
6	
7	#include <sys/types.h>
8	
9	#ifdef __EMSCRIPTEN__
10	# include <emscripten.h>
11	#endif
12	
13	#include "core.h"
14	#include "crypto_stream_chacha20.h"
15	#include "randombytes.h"
16	#ifdef RANDOMBYTES_DEFAULT_IMPLEMENTATION
17	# include "randombytes_default.h"
18	#else
19	# ifdef __native_client__
20	#  include "randombytes_nativeclient.h"
21	# else
22	#  include "randombytes_sysrandom.h"
23	# endif
24	#endif
25	#include "private/common.h"
26	
27	/* C++Builder defines a "random" macro */
28	#undef random
29	
30	static const randombytes_implementation *implementation;
31	
32	#ifndef RANDOMBYTES_DEFAULT_IMPLEMENTATION
33	# ifdef __EMSCRIPTEN__
34	#  define RANDOMBYTES_DEFAULT_IMPLEMENTATION NULL
35	# else
36	#  ifdef __native_client__
37	#   define RANDOMBYTES_DEFAULT_IMPLEMENTATION &randombytes_nativeclient_implementation;
38	#  else
39	#   define RANDOMBYTES_DEFAULT_IMPLEMENTATION &randombytes_sysrandom_implementation;
40	#  endif
41	# endif
42	#endif
43	
44	static void
45	randombytes_init_if_needed(void)
46	{
47	    if (implementation == NULL) {
48	        implementation = RANDOMBYTES_DEFAULT_IMPLEMENTATION;
49	        randombytes_stir();
50	    }
51	}
52	
53	int
54	randombytes_set_implementation(randombytes_implementation *impl)
55	{
56	    implementation = impl;
57	
58	    return 0;
59	}
60	
61	const char *
62	randombytes_implementation_name(void)
63	{
64	#ifndef __EMSCRIPTEN__
65	    randombytes_init_if_needed();
66	    return implementation->implementation_name();
67	#else
68	    return "js";
69	#endif
70	}
71	
72	uint32_t
73	randombytes_random(void)
74	{
75	#ifndef __EMSCRIPTEN__
76	    randombytes_init_if_needed();
77	    return implementation->random();
78	#else
79	    return EM_ASM_INT_V({
80	        return Module.getRandomValue();
81	    });
82	#endif
83	}
84	
85	void
86	randombytes_stir(void)
87	{
88	#ifndef __EMSCRIPTEN__
89	    randombytes_init_if_needed();
90	    if (implementation->stir != NULL) {
91	        implementation->stir();
92	    }
93	#else
94	    EM_ASM({
95	        if (Module.getRandomValue === undefined) {
96	            try {
97	                var window_ = 'object' === typeof window ? window : self;
98	                var crypto_ = typeof window_.crypto !== 'undefined' ? window_.crypto : window_.msCrypto;
99	                var randomValuesStandard = function() {
100	                    var buf = new Uint32Array(1);
101	                    crypto_.getRandomValues(buf);
102	                    return buf[0] >>> 0;
103	                };
104	                randomValuesStandard();
105	                Module.getRandomValue = randomValuesStandard;
106	            } catch (e) {
107	                try {
108	                    var crypto = require('crypto');
109	                    var randomValueNodeJS = function() {
110	                        var buf = crypto['randomBytes'](4);
111	                        return (buf[0] << 24 | buf[1] << 16 | buf[2] << 8 | buf[3]) >>> 0;
112	                    };
113	                    randomValueNodeJS();
114	                    Module.getRandomValue = randomValueNodeJS;
115	                } catch (e) {
116	                    throw 'No secure random number generator found';
117	                }
118	            }
119	        }
120	    });
121	#endif
122	}
123	
124	uint32_t
125	randombytes_uniform(const uint32_t upper_bound)
126	{
127	    uint32_t min;
128	    uint32_t r;
129	
130	#ifndef __EMSCRIPTEN__
131	    randombytes_init_if_needed();
132	    if (implementation->uniform != NULL) {
133	        return implementation->uniform(upper_bound);
134	    }
135	#endif
136	    if (upper_bound < 2) {
137	        return 0;
138	    }
139	    min = (1U + ~upper_bound) % upper_bound; /* = 2**32 mod upper_bound */
140	    do {
141	        r = randombytes_random();
142	    } while (r < min);
143	    /* r is now clamped to a set whose size mod upper_bound == 0
144	     * the worst case (2**31+1) requires ~ 2 attempts */
145	
146	    return r % upper_bound;
147	}
148	
149	void
150	randombytes_buf(void * const buf, const size_t size)
151	{
152	#ifndef __EMSCRIPTEN__
153	    randombytes_init_if_needed();
154	    if (size > (size_t) 0U) {
155	        implementation->buf(buf, size);
156	    }
157	#else
158	    unsigned char *p = (unsigned char *) buf;
159	    size_t         i;
160	
161	    for (i = (size_t) 0U; i < size; i++) {
162	        p[i] = (unsigned char) randombytes_random();
163	    }
164	#endif
165	}
166	
167	void
168	randombytes_buf_deterministic(void * const buf, const size_t size,
169	                              const unsigned char seed[randombytes_SEEDBYTES])
170	{
171	    static const unsigned char nonce[crypto_stream_chacha20_ietf_NONCEBYTES] = {
172	        'L', 'i', 'b', 's', 'o', 'd', 'i', 'u', 'm', 'D', 'R', 'G'
173	    };
174	
175	    COMPILER_ASSERT(randombytes_SEEDBYTES == crypto_stream_chacha20_ietf_KEYBYTES);
176	#if SIZE_MAX > 0x4000000000ULL
177	    COMPILER_ASSERT(randombytes_BYTES_MAX <= 0x4000000000ULL);
178	    if (size > 0x4000000000ULL) {
179	        sodium_misuse();
180	    }
181	#endif
182	    crypto_stream_chacha20_ietf((unsigned char *) buf, (unsigned long long) size,
183	                                nonce, seed);
184	}
185	
186	size_t
187	randombytes_seedbytes(void)
188	{
189	    return randombytes_SEEDBYTES;
190	}
191	
192	int
193	randombytes_close(void)
194	{
195	    if (implementation != NULL && implementation->close != NULL) {
196	        return implementation->close();
197	    }
198	    return 0;
199	}
200	
201	void
202	randombytes(unsigned char * const buf, const unsigned long long buf_len)
203	{
204	    assert(buf_len <= SIZE_MAX);
205	    randombytes_buf(buf, (size_t) buf_len);
206	}
```

**`freebsd/netinet6/nd6_nbr.c`** — ip6_sprintf(calls), calls(calls), in6_setscope(calls), nd6_na_output_fib(calls), ifa_free(calls), m_freem(calls), nd6_ns_input(function), if_name(calls), m_pullup(calls), nd6_is_addr_neighbor(calls), nd6_option_init(calls), nd6_options(calls), in6ifa_ifpwithaddr(calls), nd6_proxy_fill_sdl(calls), nd6_dad_ns_input(calls), +2 more

```c
123	 * Based on RFC 2461
124	 * Based on RFC 2462 (duplicate address detection)
125	 */
126	void
127	nd6_ns_input(struct mbuf *m, int off, int icmp6len)
128	{
129		struct ifnet *ifp;
130		struct ip6_hdr *ip6;
131		struct nd_neighbor_solicit *nd_ns;
132		struct in6_addr daddr6, myaddr6, saddr6, taddr6;
133		struct ifaddr *ifa;
134		struct sockaddr_dl proxydl;
135		union nd_opts ndopts;
136		char ip6bufs[INET6_ADDRSTRLEN], ip6bufd[INET6_ADDRSTRLEN];
137		char *lladdr;
138		int anycast, lladdrlen, proxy, rflag, tentative, tlladdr;
139	
140		ifa = NULL;
141	
142		/* RFC 6980: Nodes MUST silently ignore fragments */
143		if(m->m_flags & M_FRAGMENTED)
144			goto freeit;
145	
146		ifp = m->m_pkthdr.rcvif;
147		ip6 = mtod(m, struct ip6_hdr *);
148		if (__predict_false(ip6->ip6_hlim != 255)) {
149			ICMP6STAT_INC(icp6s_invlhlim);
150			nd6log((LOG_ERR,
151			    "nd6_ns_input: invalid hlim (%d) from %s to %s on %s\n",
152			    ip6->ip6_hlim, ip6_sprintf(ip6bufs, &ip6->ip6_src),
153			    ip6_sprintf(ip6bufd, &ip6->ip6_dst), if_name(ifp)));
154			goto bads;
155		}
156	
157		if (m->m_len < off + icmp6len) {
158			m = m_pullup(m, off + icmp6len);
159			if (m == NULL) {
160				IP6STAT_INC(ip6s_exthdrtoolong);
161				return;
162			}
163		}
164		ip6 = mtod(m, struct ip6_hdr *);
165		nd_ns = (struct nd_neighbor_solicit *)((caddr_t)ip6 + off);
166	
167		saddr6 = ip6->ip6_src;
168		daddr6 = ip6->ip6_dst;
169		taddr6 = nd_ns->nd_ns_target;
170		if (in6_setscope(&taddr6, ifp, NULL) != 0)
171			goto bad;
172	
173		rflag = (V_ip6_forwarding) ? ND_NA_FLAG_ROUTER : 0;
174		if (ND_IFINFO(ifp)->flags & ND6_IFF_ACCEPT_RTADV && V_ip6_norbit_raif)
175			rflag = 0;
176	
177		if (IN6_IS_ADDR_UNSPECIFIED(&saddr6)) {
178			/* dst has to be a solicited node multicast address. */
179			if (daddr6.s6_addr16[0] == IPV6_ADDR_INT16_MLL &&
180			    /* don't check ifindex portion */
181			    daddr6.s6_addr32[1] == 0 &&
182			    daddr6.s6_addr32[2] == IPV6_ADDR_INT32_ONE &&
183			    daddr6.s6_addr8[12] == 0xff) {
184				; /* good */
185			} else {
186				nd6log((LOG_INFO, "nd6_ns_input: bad DAD packet "
187				    "(wrong ip6 dst)\n"));
188				goto bad;
189			}
190		} else if (!V_nd6_onlink_ns_rfc4861) {
191			struct sockaddr_in6 src_sa6;
192	
193			/*
194			 * According to recent IETF discussions, it is not a good idea
195			 * to accept a NS from an address which would not be deemed
196			 * to be a neighbor otherwise.  This point is expected to be
197			 * clarified in future revisions of the specification.
198			 */
199			bzero(&src_sa6, sizeof(src_sa6));
200			src_sa6.sin6_family = AF_INET6;
201			src_sa6.sin6_len = sizeof(src_sa6);
202			src_sa6.sin6_addr = saddr6;
203			if (nd6_is_addr_neighbor(&src_sa6, ifp) == 0) {
204				nd6log((LOG_INFO, "nd6_ns_input: "
205					"NS packet from non-neighbor\n"));
206				goto bad;
207			}
208		}
209	
210		if (IN6_IS_ADDR_MULTICAST(&taddr6)) {
211			nd6log((LOG_INFO, "nd6_ns_input: bad NS target (multicast)\n"));
212			goto bad;
213		}
214	
215		icmp6len -= sizeof(*nd_ns);
216		nd6_option_init(nd_ns + 1, icmp6len, &ndopts);
217		if (nd6_options(&ndopts) < 0) {
218			nd6log((LOG_INFO,
219			    "nd6_ns_input: invalid ND option, ignored\n"));
220			/* nd6_options have incremented stats */
221			goto freeit;
222		}
223	
224		lladdr = NULL;
225		lladdrlen = 0;
226		if (ndopts.nd_opts_src_lladdr) {
227			lladdr = (char *)(ndopts.nd_opts_src_lladdr + 1);
228			lladdrlen = ndopts.nd_opts_src_lladdr->nd_opt_len << 3;
229		}
230	
231		if (IN6_IS_ADDR_UNSPECIFIED(&ip6->ip6_src) && lladdr) {
232			nd6log((LOG_INFO, "nd6_ns_input: bad DAD packet "
233			    "(link-layer address option)\n"));
234			goto bad;
235		}
236	
237		/*
238		 * Attaching target link-layer address to the NA?
239		 * (RFC 2461 7.2.4)
240		 *
241		 * NS IP dst is unicast/anycast			MUST NOT add
242		 * NS IP dst is solicited-node multicast	MUST add
243		 *
244		 * In implementation, we add target link-layer address by default.
245		 * We do not add one in MUST NOT cases.
246		 */
247		if (!IN6_IS_ADDR_MULTICAST(&daddr6))
248			tlladdr = 0;
249		else
250			tlladdr = 1;
251	
252		/*
253		 * Target address (taddr6) must be either:
254		 * (1) Valid unicast/anycast address for my receiving interface,
255		 * (2) Unicast address for which I'm offering proxy service, or
256		 * (3) "tentative" address on which DAD is being performed.
257		 */
258		/* (1) and (3) check. */
259		if (ifp->if_carp)
260			ifa = (*carp_iamatch6_p)(ifp, &taddr6);
261		else
262			ifa = (struct ifaddr *)in6ifa_ifpwithaddr(ifp, &taddr6);
263	
264		/* (2) check. */
265		proxy = 0;
266		if (ifa == NULL) {
267			if ((ifa = nd6_proxy_fill_sdl(ifp, &taddr6, &proxydl)) != NULL)
268				proxy = 1;
269		}
270		if (ifa == NULL) {
271			/*
272			 * We've got an NS packet, and we don't have that address
273			 * assigned for us.  We MUST silently ignore it.
274			 * See RFC2461 7.2.3.
275			 */
276			goto freeit;
277		}
278		myaddr6 = *IFA_IN6(ifa);
279		anycast = ((struct in6_ifaddr *)ifa)->ia6_flags & IN6_IFF_ANYCAST;
280		tentative = ((struct in6_ifaddr *)ifa)->ia6_flags & IN6_IFF_TENTATIVE;
281		if (((struct in6_ifaddr *)ifa)->ia6_flags & IN6_IFF_DUPLICATED)
282			goto freeit;
283	
284		if (lladdr && ((ifp->if_addrlen + 2 + 7) & ~7) != lladdrlen) {
285			nd6log((LOG_INFO, "nd6_ns_input: lladdrlen mismatch for %s "
286			    "(if %d, NS packet %d)\n",
287			    ip6_sprintf(ip6bufs, &taddr6),
288			    ifp->if_addrlen, lladdrlen - 2));
289			goto bad;
290		}
291	
292		if (IN6_ARE_ADDR_EQUAL(&myaddr6, &saddr6)) {
293			nd6log((LOG_INFO, "nd6_ns_input: duplicate IP6 address %s\n",
294			    ip6_sprintf(ip6bufs, &saddr6)));
295			goto freeit;
296		}
297	
298		/*
299		 * We have neighbor solicitation packet, with target address equals to
300		 * one of my tentative address.
301		 *
302		 * src addr	how to process?
303		 * ---		---
304		 * multicast	of course, invalid (rejected in ip6_input)
305		 * unicast	somebody is doing address resolution -> ignore
306		 * unspec	dup address detection
307		 *
308		 * The processing is defined in RFC 2462.
309		 */
310		if (tentative) {
311			/*
312			 * If source address is unspecified address, it is for
313			 * duplicate address detection.
314			 *
315			 * If not, the packet is for addess resolution;
316			 * silently ignore it.
317			 */
318			if (IN6_IS_ADDR_UNSPECIFIED(&saddr6))
319				nd6_dad_ns_input(ifa, ndopts.nd_opts_nonce);
320	
321			goto freeit;
322		}
323	
324		/*
325		 * If the source address is unspecified address, entries must not
326		 * be created or updated.
327		 * It looks that sender is performing DAD.  Output NA toward
328		 * all-node multicast address, to tell the sender that I'm using
329		 * the address.
330		 * S bit ("solicited") must be zero.
331		 */
332		if (IN6_IS_ADDR_UNSPECIFIED(&saddr6)) {
333			struct in6_addr in6_all;
334	
335			in6_all = in6addr_linklocal_allnodes;
336			if (in6_setscope(&in6_all, ifp, NULL) != 0)
337				goto bad;
338			nd6_na_output_fib(ifp, &in6_all, &taddr6,
339			    ((anycast || proxy || !tlladdr) ? 0 : ND_NA_FLAG_OVERRIDE) |
340			    rflag, tlladdr, proxy ? (struct sockaddr *)&proxydl : NULL,
341			    M_GETFIB(m));
342			goto freeit;
343		}
344	
345		nd6_cache_lladdr(ifp, &saddr6, lladdr, lladdrlen,
346		    ND_NEIGHBOR_SOLICIT, 0);
347	
348		nd6_na_output_fib(ifp, &saddr6, &taddr6,
349		    ((anycast || proxy || !tlladdr) ? 0 : ND_NA_FLAG_OVERRIDE) |
350		    rflag | ND_NA_FLAG_SOLICITED, tlladdr,
351		    proxy ? (struct sockaddr *)&proxydl : NULL, M_GETFIB(m));
352	 freeit:
353		if (ifa != NULL)
354			ifa_free(ifa);
355		m_freem(m);
356		return;
357	
358	 bad:
359		nd6log((LOG_ERR, "nd6_ns_input: src=%s\n",
360			ip6_sprintf(ip6bufs, &saddr6)));
361		nd6log((LOG_ERR, "nd6_ns_input: dst=%s\n",
362			ip6_sprintf(ip6bufs, &daddr6)));
363		nd6log((LOG_ERR, "nd6_ns_input: tgt=%s\n",
364			ip6_sprintf(ip6bufs, &taddr6)));
365	 bads:
366		ICMP6STAT_INC(icp6s_badns);
367		if (ifa != NULL)
368			ifa_free(ifa);
369		m_freem(m);
370	}
371	
372	static struct ifaddr *
373	nd6_proxy_fill_sdl(struct ifnet *ifp, const struct in6_addr *taddr6,
374	    struct sockaddr_dl *sdl)
375	{
376		struct ifaddr *ifa;
377		struct llentry *ln;
378	
379		ifa = NULL;
380		ln = nd6_lookup(taddr6, LLE_SF(AF_INET6, 0), ifp);
381		if (ln == NULL)
382			return (ifa);
383		if ((ln->la_flags & (LLE_PUB | LLE_VALID)) == (LLE_PUB | LLE_VALID)) {
384			link_init_sdl(ifp, (struct sockaddr *)sdl, ifp->if_type);
385			sdl->sdl_alen = ifp->if_addrlen;
386			bcopy(ln->ll_addr, &sdl->sdl_data, ifp->if_addrlen);
387			LLE_RUNLOCK(ln);
388			ifa = (struct ifaddr *)in6ifa_ifpforlinklocal(ifp,
389			    IN6_IFF_NOTREADY|IN6_IFF_ANYCAST);
390		} else
391			LLE_RUNLOCK(ln);
392	
393		return (ifa);
394	}
395	
396	/*
397	 * Output a Neighbor Solicitation Message. Caller specifies:
```


... (output truncated to budget; the source above is complete and verbatim — treat it as already Read. For any area not covered, run another codegraph_explore with the specific names — do NOT Read these files.)

## finding-c24e5161cb3f — 缺少有状态 DHCPv6 地址配置支持

Query: `Trace the implementation and all relevant callers for 缺少有状态 DHCPv6 地址配置支持. Start from freebsd/netinet6/icmp6.c symbol ni6_store_addrs. Look specifically for an alternative implementation or counterevidence that would make the suspected design-to-code difference invalid.`

**Dynamic-dispatch links among your symbols**
(synthesized — the indirect hops grep/Read would reconstruct; the `@file:line` is the wiring site)

- ng_generic_msg → ngs_rcvmsg   [dynamic: fn-pointer ng_type.rcvmsg @freebsd/netgraph/ng_base.c:2934]

> Full source for these symbols is below — the call flow among them, followed by their bodies.
**Exploration: Trace the implementation and all relevant callers for 缺少有状态 DHCPv6 地址配置支持. Start from freebsd/netinet6/icmp6.c symbol ni6_store_addrs. Look specifically for an alternative implementation or counterevidence that would make the suspected design-to-code difference invalid.**

Found 26 symbols across 4 files.

**Blast radius — what depends on these (update/verify before editing)**

- `ni6_store_addrs` (freebsd/netinet6/icmp6.c:1745) — 1 caller in `freebsd/netinet6/icmp6.c`; ⚠️ no covering tests found
- `make` (freebsd/contrib/libsodium/packaging/dotnet-core/prepare.py:67) — 1 caller in `freebsd/contrib/libsodium/packaging/dotnet-core/prepare.py`; ⚠️ no covering tests found

**Relationships**

**calls:**
- ni6_store_addrs → in6_addrscope
- ni6_store_addrs → in6_clearscope
- ni6_input → ni6_store_addrs
- ni6_addrs → in6_addrscope
- in6_ifawithifp → in6_addrscope
- in6_selectsrc → in6_addrscope
- nd6_lle_event → in6_addrscope
- scope6_addr2default → in6_addrscope
- in6_setscope → in6_addrscope
- sa6_checkzone → in6_addrscope
- sa6_checkzone_ifp → in6_addrscope
- sctp_notify_peer_addr_change → in6_clearscope
- sctp_recover_scope → in6_clearscope
- sctp_addr_in_initack → in6_clearscope
- sctp_add_addr_to_mbuf → in6_clearscope
- ... and 35 more

**instantiates:**
- main → WindowsItem
- main → Version
- main → MacOSItem
- main → LinuxItem
- main → ExtraItem

**references:**
- main → MAKEFILE
- main → DOCKER
- main → PROPSFILE
- main → EXTRAS
- main → LINUX
- main → MACOS
- main → WINDOWS
- __init__ → LIBRARY
- __init__ → CACHEDIR
- __init__ → LIBRARY
- __init__ → CACHEDIR
- make → DOCKER
- __init__ → LIBRARY
- __init__ → CACHEDIR
- __init__ → CACHEDIR

**Source Code**

> The code below is the **verbatim, current on-disk source** of these files — re-read from disk on this call and line-numbered, byte-for-byte identical to what the Read tool returns. It is NOT a summary, outline, or stale cache. Treat each block as a Read you have already performed: do not Read a file shown here.

**`freebsd/contrib/libsodium/src/libsodium/randombytes/randombytes.c`** — implementation(constant)

```c
1	
2	#include <assert.h>
3	#include <limits.h>
4	#include <stdint.h>
5	#include <stdlib.h>
6	
7	#include <sys/types.h>
8	
9	#ifdef __EMSCRIPTEN__
10	# include <emscripten.h>
11	#endif
12	
13	#include "core.h"
14	#include "crypto_stream_chacha20.h"
15	#include "randombytes.h"
16	#ifdef RANDOMBYTES_DEFAULT_IMPLEMENTATION
17	# include "randombytes_default.h"
18	#else
19	# ifdef __native_client__
20	#  include "randombytes_nativeclient.h"
21	# else
22	#  include "randombytes_sysrandom.h"
23	# endif
24	#endif
25	#include "private/common.h"
26	
27	/* C++Builder defines a "random" macro */
28	#undef random
29	
30	static const randombytes_implementation *implementation;
31	
32	#ifndef RANDOMBYTES_DEFAULT_IMPLEMENTATION
33	# ifdef __EMSCRIPTEN__
34	#  define RANDOMBYTES_DEFAULT_IMPLEMENTATION NULL
35	# else
36	#  ifdef __native_client__
37	#   define RANDOMBYTES_DEFAULT_IMPLEMENTATION &randombytes_nativeclient_implementation;
38	#  else
39	#   define RANDOMBYTES_DEFAULT_IMPLEMENTATION &randombytes_sysrandom_implementation;
40	#  endif
41	# endif
42	#endif
43	
44	static void
45	randombytes_init_if_needed(void)
46	{
47	    if (implementation == NULL) {
48	        implementation = RANDOMBYTES_DEFAULT_IMPLEMENTATION;
49	        randombytes_stir();
50	    }
51	}
52	
53	int
54	randombytes_set_implementation(randombytes_implementation *impl)
55	{
56	    implementation = impl;
57	
58	    return 0;
59	}
60	
61	const char *
62	randombytes_implementation_name(void)
63	{
64	#ifndef __EMSCRIPTEN__
65	    randombytes_init_if_needed();
66	    return implementation->implementation_name();
67	#else
68	    return "js";
69	#endif
70	}
71	
72	uint32_t
73	randombytes_random(void)
74	{
75	#ifndef __EMSCRIPTEN__
76	    randombytes_init_if_needed();
77	    return implementation->random();
78	#else
79	    return EM_ASM_INT_V({
80	        return Module.getRandomValue();
81	    });
82	#endif
83	}
84	
85	void
86	randombytes_stir(void)
87	{
88	#ifndef __EMSCRIPTEN__
89	    randombytes_init_if_needed();
90	    if (implementation->stir != NULL) {
91	        implementation->stir();
92	    }
93	#else
94	    EM_ASM({
95	        if (Module.getRandomValue === undefined) {
96	            try {
97	                var window_ = 'object' === typeof window ? window : self;
98	                var crypto_ = typeof window_.crypto !== 'undefined' ? window_.crypto : window_.msCrypto;
99	                var randomValuesStandard = function() {
100	                    var buf = new Uint32Array(1);
101	                    crypto_.getRandomValues(buf);
102	                    return buf[0] >>> 0;
103	                };
104	                randomValuesStandard();
105	                Module.getRandomValue = randomValuesStandard;
106	            } catch (e) {
107	                try {
108	                    var crypto = require('crypto');
109	                    var randomValueNodeJS = function() {
110	                        var buf = crypto['randomBytes'](4);
111	                        return (buf[0] << 24 | buf[1] << 16 | buf[2] << 8 | buf[3]) >>> 0;
112	                    };
113	                    randomValueNodeJS();
114	                    Module.getRandomValue = randomValueNodeJS;
115	                } catch (e) {
116	                    throw 'No secure random number generator found';
117	                }
118	            }
119	        }
120	    });
121	#endif
122	}
123	
124	uint32_t
125	randombytes_uniform(const uint32_t upper_bound)
126	{
127	    uint32_t min;
128	    uint32_t r;
129	
130	#ifndef __EMSCRIPTEN__
131	    randombytes_init_if_needed();
132	    if (implementation->uniform != NULL) {
133	        return implementation->uniform(upper_bound);
134	    }
135	#endif
136	    if (upper_bound < 2) {
137	        return 0;
138	    }
139	    min = (1U + ~upper_bound) % upper_bound; /* = 2**32 mod upper_bound */
140	    do {
141	        r = randombytes_random();
142	    } while (r < min);
143	    /* r is now clamped to a set whose size mod upper_bound == 0
144	     * the worst case (2**31+1) requires ~ 2 attempts */
145	
146	    return r % upper_bound;
147	}
148	
149	void
150	randombytes_buf(void * const buf, const size_t size)
151	{
152	#ifndef __EMSCRIPTEN__
153	    randombytes_init_if_needed();
154	    if (size > (size_t) 0U) {
155	        implementation->buf(buf, size);
156	    }
157	#else
158	    unsigned char *p = (unsigned char *) buf;
159	    size_t         i;
160	
161	    for (i = (size_t) 0U; i < size; i++) {
162	        p[i] = (unsigned char) randombytes_random();
163	    }
164	#endif
165	}
166	
167	void
168	randombytes_buf_deterministic(void * const buf, const size_t size,
169	                              const unsigned char seed[randombytes_SEEDBYTES])
170	{
171	    static const unsigned char nonce[crypto_stream_chacha20_ietf_NONCEBYTES] = {
172	        'L', 'i', 'b', 's', 'o', 'd', 'i', 'u', 'm', 'D', 'R', 'G'
173	    };
174	
175	    COMPILER_ASSERT(randombytes_SEEDBYTES == crypto_stream_chacha20_ietf_KEYBYTES);
176	#if SIZE_MAX > 0x4000000000ULL
177	    COMPILER_ASSERT(randombytes_BYTES_MAX <= 0x4000000000ULL);
178	    if (size > 0x4000000000ULL) {
179	        sodium_misuse();
180	    }
181	#endif
182	    crypto_stream_chacha20_ietf((unsigned char *) buf, (unsigned long long) size,
183	                                nonce, seed);
184	}
185	
186	size_t
187	randombytes_seedbytes(void)
188	{
189	    return randombytes_SEEDBYTES;
190	}
191	
192	int
193	randombytes_close(void)
194	{
195	    if (implementation != NULL && implementation->close != NULL) {
196	        return implementation->close();
197	    }
198	    return 0;
199	}
200	
201	void
202	randombytes(unsigned char * const buf, const unsigned long long buf_len)
203	{
204	    assert(buf_len <= SIZE_MAX);
205	    randombytes_buf(buf, (size_t) buf_len);
206	}
```

**`freebsd/contrib/libsodium/packaging/dotnet-core/prepare.py`** — make(method), WindowsItem(class), main(function), __init__(method), Version(class), MacOSItem(class), LinuxItem(class), ExtraItem(class), MAKEFILE(variable), DOCKER(variable), PROPSFILE(variable), EXTRAS(variable), LINUX(variable), MACOS(variable), WINDOWS(variable), +2 more

```python
1	#!/usr/bin/env python3
2	
3	import os.path
4	import re
5	import sys
6	
7	WINDOWS = [
8	  # --------------------- ----------------- #
9	  # Runtime ID            Platform          #
10	  # --------------------- ----------------- #
11	  ( 'win-x64',            'x64'             ),
12	  ( 'win-x86',            'Win32'           ),
13	  # --------------------- ----------------- #
14	]
15	
16	MACOS = [
17	  # --------------------- ----------------- #
18	  # Runtime ID            Codename          #
19	  # --------------------- ----------------- #
20	  ( 'osx-x64',            'sierra'          ),
21	  # --------------------- ----------------- #
22	]
23	
24	LINUX = [
25	  # --------------------- ----------------- #
26	  # Runtime ID            Docker Image      #
27	  # --------------------- ----------------- #
28	  ( 'linux-x64',          'debian:stretch'  ),
29	  # --------------------- ----------------- #
30	]
31	
32	EXTRAS = [ 'LICENSE', 'AUTHORS', 'ChangeLog' ]
33	
34	PROPSFILE = 'libsodium.props'
35	MAKEFILE = 'Makefile'
36	BUILDDIR = 'build'
37	CACHEDIR = 'cache'
38	TEMPDIR = 'temp'
39	
40	PACKAGE = 'libsodium'
41	LIBRARY = 'libsodium'
42	
43	DOCKER = 'sudo docker'
44	
45	class Version:
46	
47	  def __init__(self, libsodium_version, package_version):
48	    self.libsodium_version = libsodium_version
49	    self.package_version = package_version
50	
51	    self.builddir = os.path.join(BUILDDIR, libsodium_version)
52	    self.tempdir = os.path.join(TEMPDIR, libsodium_version)
53	    self.projfile = os.path.join(self.builddir, '{0}.{1}.pkgproj'.format(PACKAGE, package_version))
54	    self.propsfile = os.path.join(self.builddir, '{0}.props'.format(PACKAGE))
55	    self.pkgfile = os.path.join(BUILDDIR, '{0}.{1}.nupkg'.format(PACKAGE, package_version))
56	
57	class WindowsItem:
58	
59	  def __init__(self, version, rid, platform):
60	    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}-msvc.zip'.format(version.libsodium_version)
61	    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
62	    self.packfile = os.path.join(version.builddir, 'runtimes', rid, 'native', LIBRARY + '.dll')
63	    self.itemfile = '{0}/Release/v140/dynamic/libsodium.dll'.format(platform)
64	    self.tempdir = os.path.join(version.tempdir, rid)
65	    self.tempfile = os.path.join(self.tempdir, os.path.normpath(self.itemfile))
66	
67	  def make(self, f):
68	    f.write('\n')
69	    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
70	    f.write('\t@mkdir -p $(dir $@)\n')
71	    f.write('\tcp -f $< $@\n')
72	    f.write('\n')
73	    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
74	    f.write('\t@mkdir -p $(dir $@)\n')
75	    f.write('\tcd {0} && unzip -q -DD -o {1} \'{2}\'\n'.format(
76	      self.tempdir,
77	      os.path.relpath(self.cachefile, self.tempdir),
78	      self.itemfile
79	    ))
80	
81	class MacOSItem:
82	
83	  def __init__(self, version, rid, codename):
84	    self.url = 'https://bintray.com/homebrew/bottles/download_file?file_path=libsodium-{0}.{1}.bottle.tar.gz'.format(version.libsodium_version, codename)
85	    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
86	    self.packfile = os.path.join(version.builddir, 'runtimes', rid, 'native', LIBRARY + '.dylib')
87	    self.itemfile = 'libsodium/{0}/lib/libsodium.dylib'.format(version.libsodium_version)
88	    self.tempdir = os.path.join(version.tempdir, rid)
89	    self.tempfile = os.path.join(self.tempdir, os.path.normpath(self.itemfile))
90	
91	  def make(self, f):
92	    f.write('\n')
93	    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
94	    f.write('\t@mkdir -p $(dir $@)\n')
95	    f.write('\tcp -f $< $@\n')
96	    f.write('\n')
97	    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
98	    f.write('\t@mkdir -p $(dir $@)\n')
99	    f.write('\tcd {0} && tar xzmf {1} \'{2}\'\n'.format(
100	      self.tempdir,
101	      os.path.relpath(self.cachefile, self.tempdir),
102	      os.path.dirname(self.itemfile)
103	    ))
104	
105	class LinuxItem:
106	
107	  def __init__(self, version, rid, docker_image):
108	    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}.tar.gz'.format(version.libsodium_version)
109	    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
110	    self.packfile = os.path.join(version.builddir, 'runtimes', rid, 'native', LIBRARY + '.so')
111	    self.tempdir = os.path.join(version.tempdir, rid)
112	    self.tempfile = os.path.join(self.tempdir, 'libsodium.so')
113	    self.docker_image = docker_image
114	    self.recipe = rid
115	
116	  def make(self, f):
117	    recipe = self.recipe
118	    while not os.path.exists(os.path.join('recipes', recipe)):
119	      m = re.fullmatch(r'([^.-]+)((([.][^.-]+)*)[.][^.-]+)?([-].*)?', recipe)
120	      if m.group(5) is None:
121	        recipe = 'build'
122	        break
123	      elif m.group(2) is None:
124	        recipe = m.group(1)
125	      else:
126	        recipe = m.group(1) + m.group(3) + m.group(5)
127	
128	    f.write('\n')
129	    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
130	    f.write('\t@mkdir -p $(dir $@)\n')
131	    f.write('\tcp -f $< $@\n')
132	    f.write('\n')
133	    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
134	    f.write('\t@mkdir -p $(dir $@)\n')
135	    f.write('\t{0} run --rm '.format(DOCKER) +
136	            '-v $(abspath recipes):/io/recipes ' +
137	            '-v $(abspath $<):/io/libsodium.tar.gz ' +
138	            '-v $(abspath $(dir $@)):/io/output ' +
139	            '{0} sh -x -e /io/recipes/{1}\n'.format(self.docker_image, recipe))
140	
141	class ExtraItem:
142	
143	  def __init__(self, version, filename):
144	    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}.tar.gz'.format(version.libsodium_version)
145	    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
146	    self.packfile = os.path.join(version.builddir, filename)
147	    self.itemfile = 'libsodium-{0}/{1}'.format(version.libsodium_version, filename)
148	    self.tempdir = os.path.join(version.tempdir, 'extras')
149	    self.tempfile = os.path.join(self.tempdir, os.path.normpath(self.itemfile))
150	
151	  def make(self, f):
152	    f.write('\n')
153	    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
154	    f.write('\t@mkdir -p $(dir $@)\n')
155	    f.write('\tcp -f $< $@\n')
156	    f.write('\n')
157	    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
158	    f.write('\t@mkdir -p $(dir $@)\n')
159	    f.write('\tcd {0} && tar xzmf {1} \'{2}\'\n'.format(
160	      self.tempdir,
161	      os.path.relpath(self.cachefile, self.tempdir),
162	      self.itemfile
163	    ))
164	
165	def main(args):
166	  m = re.fullmatch(r'((\d+\.\d+\.\d+)(\.\d+)?)(?:-(\w+(?:[_.-]\w+)*))?', args[1]) if len(args) == 2 else None
167	
168	  if m is None:
169	    print('Usage:')
170	    print('       python3 prepare.py <version>')
171	    print()
172	    print('Examples:')
173	    print('       python3 prepare.py 1.0.16-preview-01')
174	    print('       python3 prepare.py 1.0.16-preview-02')
175	    print('       python3 prepare.py 1.0.16-preview-03')
176	    print('       python3 prepare.py 1.0.16')
177	    print('       python3 prepare.py 1.0.16.1-preview-01')
178	    print('       python3 prepare.py 1.0.16.1')
179	    print('       python3 prepare.py 1.0.16.2')
180	    return 1
181	
182	  version = Version(m.group(2), m.group(0))
183	
184	  items = [ WindowsItem(version, rid, platform)   for (rid, platform) in WINDOWS   ] + \
185	          [ MacOSItem(version, rid, codename)     for (rid, codename) in MACOS     ] + \
186	          [ LinuxItem(version, rid, docker_image) for (rid, docker_image) in LINUX ] + \
187	          [ ExtraItem(version, filename)          for filename in EXTRAS           ]
188	
189	  downloads = {item.cachefile: item.url for item in items}
190	
191	  with open(MAKEFILE, 'w') as f:
192	    f.write('all: {0}\n'.format(version.pkgfile))
193	
194	    for download in sorted(downloads):
195	      f.write('\n')
196	      f.write('{0}:\n'.format(download))
197	      f.write('\t@mkdir -p $(dir $@)\n')
198	      f.write('\tcurl -f#Lo $@ \'{0}\'\n'.format(downloads[download]))
199	
200	    for item in items:
201	      item.make(f)
202	
203	    f.write('\n')
204	    f.write('{0}: {1}\n'.format(version.propsfile, PROPSFILE))
205	    f.write('\t@mkdir -p $(dir $@)\n')
206	    f.write('\tcp -f $< $@\n')
207	
208	    f.write('\n')
209	    f.write('{0}: {1}\n'.format(version.projfile, version.propsfile))
210	    f.write('\t@mkdir -p $(dir $@)\n')
211	    f.write('\techo \'' +
212	            '<Project Sdk="Microsoft.NET.Sdk">' +
213	            '<Import Project="{0}" />'.format(os.path.relpath(version.propsfile, os.path.dirname(version.projfile))) +
214	            '<PropertyGroup>' +
215	            '<Version>{0}</Version>'.format(version.package_version) +
216	            '</PropertyGroup>' +
217	            '</Project>\' > $@\n')
218	
219	    f.write('\n')
220	    f.write('{0}:'.format(version.pkgfile))
221	    f.write(' \\\n\t\t{0}'.format(version.projfile))
222	    f.write(' \\\n\t\t{0}'.format(version.propsfile))
223	    for item in items:
224	      f.write(' \\\n\t\t{0}'.format(item.packfile))
225	    f.write('\n')
226	    f.write('\t@mkdir -p $(dir $@)\n')
227	    f.write('\t{0} run --rm '.format(DOCKER) +
228	            '-v $(abspath recipes):/io/recipes ' +
229	            '-v $(abspath $(dir $<)):/io/input ' +
230	            '-v $(abspath $(dir $@)):/io/output ' +
231	            '{0} sh -x -e /io/recipes/{1} {2}\n'.format('microsoft/dotnet:2.0-sdk', 'pack', os.path.relpath(version.projfile, version.builddir)))
232	
233	    f.write('\n')
234	    f.write('test: {0}\n'.format(version.pkgfile))
235	    f.write('\t{0} run --rm '.format(DOCKER) +
236	            '-v $(abspath recipes):/io/recipes ' +
237	            '-v $(abspath $(dir $<)):/io/packages ' +
238	            '{0} sh -x -e /io/recipes/{1} "{2}"\n'.format('microsoft/dotnet:2.0-sdk', 'test', version.package_version))
239	
240	  print('prepared', MAKEFILE, 'to make', version.pkgfile, 'for libsodium', version.libsodium_version)
241	  return 0
242	
243	if __name__ == '__main__':
244	  sys.exit(main(sys.argv))
```

**`freebsd/contrib/libsodium/src/libsodium/crypto_onetimeauth/poly1305/onetimeauth_poly1305.c`** — implementation(constant)

```c
1	
2	#include "onetimeauth_poly1305.h"
3	#include "crypto_onetimeauth_poly1305.h"
4	#include "private/common.h"
5	#include "private/implementations.h"
6	#include "randombytes.h"
7	#include "runtime.h"
8	
9	#include "donna/poly1305_donna.h"
10	#if defined(HAVE_TI_MODE) && defined(HAVE_EMMINTRIN_H)
11	# include "sse2/poly1305_sse2.h"
12	#endif
13	
14	static const crypto_onetimeauth_poly1305_implementation *implementation =
15	    &crypto_onetimeauth_poly1305_donna_implementation;
16	
17	int
18	crypto_onetimeauth_poly1305(unsigned char *out, const unsigned char *in,
19	                            unsigned long long inlen, const unsigned char *k)
20	{
21	    return implementation->onetimeauth(out, in, inlen, k);
22	}
23	
24	int
25	crypto_onetimeauth_poly1305_verify(const unsigned char *h,
26	                                   const unsigned char *in,
27	                                   unsigned long long   inlen,
28	                                   const unsigned char *k)
29	{
30	    return implementation->onetimeauth_verify(h, in, inlen, k);
31	}
32	
33	int
34	crypto_onetimeauth_poly1305_init(crypto_onetimeauth_poly1305_state *state,
35	                                 const unsigned char *key)
36	{
37	    return implementation->onetimeauth_init(state, key);
38	}
39	
40	int
41	crypto_onetimeauth_poly1305_update(crypto_onetimeauth_poly1305_state *state,
42	                                   const unsigned char *in,
43	                                   unsigned long long inlen)
44	{
45	    return implementation->onetimeauth_update(state, in, inlen);
46	}
47	
48	int
49	crypto_onetimeauth_poly1305_final(crypto_onetimeauth_poly1305_state *state,
50	                                  unsigned char *out)
51	{
52	    return implementation->onetimeauth_final(state, out);
53	}
54	
55	size_t
56	crypto_onetimeauth_poly1305_bytes(void)
57	{
58	    return crypto_onetimeauth_poly1305_BYTES;
59	}
60	
61	size_t
62	crypto_onetimeauth_poly1305_keybytes(void)
63	{
64	    return crypto_onetimeauth_poly1305_KEYBYTES;
65	}
66	
67	size_t
68	crypto_onetimeauth_poly1305_statebytes(void)
69	{
70	    return sizeof(crypto_onetimeauth_poly1305_state);
71	}
72	
73	void
74	crypto_onetimeauth_poly1305_keygen(
75	    unsigned char k[crypto_onetimeauth_poly1305_KEYBYTES])
76	{
77	    randombytes_buf(k, crypto_onetimeauth_poly1305_KEYBYTES);
78	}
79	
80	int
81	_crypto_onetimeauth_poly1305_pick_best_implementation(void)
82	{
83	    implementation = &crypto_onetimeauth_poly1305_donna_implementation;
84	#if defined(HAVE_TI_MODE) && defined(HAVE_EMMINTRIN_H)
85	    if (sodium_runtime_has_sse2()) {
86	        implementation = &crypto_onetimeauth_poly1305_sse2_implementation;
87	    }
88	#endif
89	    return 0;
90	}
```

**`freebsd/contrib/libsodium/src/libsodium/crypto_scalarmult/curve25519/scalarmult_curve25519.c`** — implementation(constant)

```c
1	
2	#include "crypto_scalarmult_curve25519.h"
3	#include "private/implementations.h"
4	#include "scalarmult_curve25519.h"
5	#include "runtime.h"
6	
7	#ifdef HAVE_AVX_ASM
8	# include "sandy2x/curve25519_sandy2x.h"
9	#endif
10	#include "ref10/x25519_ref10.h"
11	static const crypto_scalarmult_curve25519_implementation *implementation =
12	    &crypto_scalarmult_curve25519_ref10_implementation;
13	
14	int
15	crypto_scalarmult_curve25519(unsigned char *q, const unsigned char *n,
16	                             const unsigned char *p)
17	{
18	    size_t                 i;
19	    volatile unsigned char d = 0;
20	
21	    if (implementation->mult(q, n, p) != 0) {
22	        return -1; /* LCOV_EXCL_LINE */
23	    }
24	    for (i = 0; i < crypto_scalarmult_curve25519_BYTES; i++) {
25	        d |= q[i];
26	    }
27	    return -(1 & ((d - 1) >> 8));
28	}
29	
30	int
31	crypto_scalarmult_curve25519_base(unsigned char *q, const unsigned char *n)
32	{
33	    return implementation->mult_base(q, n);
34	}
35	
36	size_t
37	crypto_scalarmult_curve25519_bytes(void)
38	{
39	    return crypto_scalarmult_curve25519_BYTES;
40	}
41	
42	size_t
43	crypto_scalarmult_curve25519_scalarbytes(void)
44	{
45	    return crypto_scalarmult_curve25519_SCALARBYTES;
46	}
47	
48	int
49	_crypto_scalarmult_curve25519_pick_best_implementation(void)
50	{
51	    implementation = &crypto_scalarmult_curve25519_ref10_implementation;
52	
53	#ifdef HAVE_AVX_ASM
54	    if (sodium_runtime_has_avx()) {
55	        implementation = &crypto_scalarmult_curve25519_sandy2x_implementation;
56	    }
57	#endif
58	    return 0;
59	}
```


... (output truncated to budget; the source above is complete and verbatim — treat it as already Read. For any area not covered, run another codegraph_explore with the specific names — do NOT Read these files.)

## finding-6118ff644d30 — 宽泛组播分支抢先返回，遮蔽后续 IPv6/MLD 分类

Query: `Trace the implementation and all relevant callers for 宽泛组播分支抢先返回，遮蔽后续 IPv6/MLD 分类. Start from lib/ff_dpdk_if.c symbol protocol_filter. Look specifically for an alternative implementation or counterevidence that would make the suspected design-to-code difference invalid.`

**Dynamic-dispatch links among your symbols**
(synthesized — the indirect hops grep/Read would reconstruct; the `@file:line` is the wiring site)

- ng_generic_msg → ngs_rcvmsg   [dynamic: fn-pointer ng_type.rcvmsg @freebsd/netgraph/ng_base.c:2934]

> Full source for these symbols is below — the call flow among them, followed by their bodies.
**Exploration: Trace the implementation and all relevant callers for 宽泛组播分支抢先返回，遮蔽后续 IPv6/MLD 分类. Start from lib/ff_dpdk_if.c symbol protocol_filter. Look specifically for an alternative implementation or counterevidence that would make the suspected design-to-code difference invalid.**

Found 29 symbols across 8 files.

**Blast radius — what depends on these (update/verify before editing)**

- `Symbol` (dpdk/buildtools/coff.py:76) — 1 caller in `dpdk/buildtools/coff.py`; ⚠️ no covering tests found

**Relationships**

**calls:**
- protocol_filter → rte_is_multicast_ether_addr
- protocol_filter → ff_kni_proto_filter
- cmd_mcast_addr_parsed → rte_is_multicast_ether_addr
- mlx5_nl_mac_addr_sync → rte_is_multicast_ether_addr
- _avp_mac_filter → rte_is_multicast_ether_addr
- bnx2x_tx_encap → rte_is_multicast_ether_addr
- ulp_rte_parser_is_bcmc_addr → rte_is_multicast_ether_addr
- cnxk_nix_mc_addr_list_configure → rte_is_multicast_ether_addr
- enicpmd_set_mc_addr_list → rte_is_multicast_ether_addr
- hns3_set_mc_addr_chk_param → rte_is_multicast_ether_addr
- hns3_configure_all_mc_mac_addr → rte_is_multicast_ether_addr
- hns3_configure_all_mac_addr → rte_is_multicast_ether_addr
- hns3_add_mac_addr → rte_is_multicast_ether_addr
- hns3_remove_mac_addr → rte_is_multicast_ether_addr
- hns3_add_mc_mac_addr → rte_is_multicast_ether_addr
- ... and 75 more

**references:**
- protocol_filter → enable_kni
- get_value → COFF_SN_ABSOLUTE
- get_value → COFF_SN_DEBUG
- get_value → COFF_SN_UNDEFINED
- ZSTD_decodeSeqHeaders → ML_defaultDTable
- ZSTD_decodeSeqHeaders → OF_defaultDTable
- ZSTD_decodeSeqHeaders → LL_defaultDTable
- pfr_pool_get → pfr_ffaddr

**instantiates:**
- symbols → Symbol
- __init__ → Image
- uni_undel → filter
- pfr_pool_get → filter

**Source Code**

> The code below is the **verbatim, current on-disk source** of these files — re-read from disk on this call and line-numbered, byte-for-byte identical to what the Read tool returns. It is NOT a summary, outline, or stale cache. Treat each block as a Read you have already performed: do not Read a file shown here.

**`lib/ff_dpdk_if.c`** — ff_kni_proto_filter(calls), enable_kni(variable), protocol_filter(function), rte_is_multicast_ether_addr(calls), filter(variable)

```c
71	#define KNI_MBUF_MAX 2048
72	#define KNI_QUEUE_SIZE KNI_MBUF_MAX
73	
74	int enable_kni = 0;
75	static int kni_accept;
76	static enum FF_KNICTL_ACTION knictl_action = FF_KNICTL_ACTION_DEFAULT;
77	#endif

... (gap) ...

1540	    ff_veth_process_packet(ctx->ifp, hdr);
1541	}
1542	
1543	static enum FilterReturn
1544	protocol_filter(const void *data, uint16_t len)
1545	{
1546	    if(len < RTE_ETHER_ADDR_LEN)
1547	        return FILTER_UNKNOWN;
1548	
1549	    const struct rte_ether_hdr *hdr;
1550	    const struct rte_vlan_hdr *vlanhdr;
1551	    hdr = (const struct rte_ether_hdr *)data;
1552	    uint16_t ether_type = rte_be_to_cpu_16(hdr->ether_type);
1553	    data += RTE_ETHER_HDR_LEN;
1554	    len -= RTE_ETHER_HDR_LEN;
1555	
1556	    if (ether_type == RTE_ETHER_TYPE_VLAN) {
1557	        vlanhdr = (struct rte_vlan_hdr *)data;
1558	        ether_type = rte_be_to_cpu_16(vlanhdr->eth_proto);
1559	        data += sizeof(struct rte_vlan_hdr);
1560	        len -= sizeof(struct rte_vlan_hdr);
1561	    }
1562	
1563	    if(ether_type == RTE_ETHER_TYPE_ARP) {
1564	        return FILTER_ARP;
1565	    }
1566	
1567	    /* Multicast protocol, such as stp(used by zebra), is forwarded to kni and has a separate speed limit */
1568	    if (rte_is_multicast_ether_addr(&hdr->dst_addr)) {
1569	        return FILTER_MULTI;
1570	    }
1571	
1572	#if (!defined(__FreeBSD__) && defined(INET6) ) || \
1573	    ( defined(__FreeBSD__) && defined(INET6) && defined(FF_KNI))
1574	    if (ether_type == RTE_ETHER_TYPE_IPV6) {
1575	        return ff_kni_proto_filter(data,
1576	            len, ether_type);
1577	    }
1578	#endif
1579	
1580	#ifndef FF_KNI
1581	    return FILTER_UNKNOWN;
1582	#else
1583	    if (!enable_kni) {
1584	        return FILTER_UNKNOWN;
1585	    }
1586	
1587	    if(ether_type != RTE_ETHER_TYPE_IPV4)
1588	        return FILTER_UNKNOWN;
1589	
1590	    return ff_kni_proto_filter(data,
1591	        len, ether_type);
1592	#endif
1593	}
1594	
1595	static inline void
1596	pktmbuf_deep_attach(struct rte_mbuf *mi, const struct rte_mbuf *m)

... (gap) ...

1743	            }
1744	        }
1745	
1746	        enum FilterReturn filter = protocol_filter(data, len);
1747	#ifdef INET6
1748	        if (filter == FILTER_ARP || filter == FILTER_NDP) {
1749	#else
```

**`dpdk/buildtools/coff.py`** — Symbol(class), __init__(method), name(method), get_value(method), symbols(method), decode_asciiz(function), get_string(method), get_section_data(method), COFF_SN_ABSOLUTE(variable), COFF_SN_DEBUG(variable), COFF_SN_UNDEFINED(variable), Image(class), _parse_strings(method)

```python
1	# SPDX-License-Identifier: BSD-3-Clause
2	# Copyright (c) 2020 Dmitry Kozlyuk <dmitry.kozliuk@gmail.com>
3	
4	import ctypes
5	
6	# x86_64 little-endian
7	COFF_MAGIC = 0x8664
8	
9	# Names up to this length are stored immediately in symbol table entries.
10	COFF_NAMELEN = 8
11	
12	# Special "section numbers" changing the meaning of symbol table entry.
13	COFF_SN_UNDEFINED = 0
14	COFF_SN_ABSOLUTE = -1
15	COFF_SN_DEBUG = -2
16	
17	
18	class CoffFileHeader(ctypes.LittleEndianStructure):
19	    _pack_ = True
20	    _fields_ = [
21	        ("magic", ctypes.c_uint16),
22	        ("section_count", ctypes.c_uint16),
23	        ("timestamp", ctypes.c_uint32),
24	        ("symbol_table_offset", ctypes.c_uint32),
25	        ("symbol_count", ctypes.c_uint32),
26	        ("optional_header_size", ctypes.c_uint16),
27	        ("flags", ctypes.c_uint16),
28	    ]
29	
30	
31	class CoffName(ctypes.Union):
32	    class Reference(ctypes.LittleEndianStructure):
33	        _pack_ = True
34	        _fields_ = [
35	            ("zeroes", ctypes.c_uint32),
36	            ("offset", ctypes.c_uint32),
37	        ]
38	
39	    Immediate = ctypes.c_char * 8
40	
41	    _pack_ = True
42	    _fields_ = [
43	        ("immediate", Immediate),
44	        ("reference", Reference),
45	    ]
46	
47	
48	class CoffSection(ctypes.LittleEndianStructure):
49	    _pack_ = True
50	    _fields_ = [
51	        ("name", CoffName),
52	        ("physical_address", ctypes.c_uint32),
53	        ("physical_address", ctypes.c_uint32),
54	        ("size", ctypes.c_uint32),
55	        ("data_offset", ctypes.c_uint32),
56	        ("relocations_offset", ctypes.c_uint32),
57	        ("line_numbers_offset", ctypes.c_uint32),
58	        ("relocation_count", ctypes.c_uint16),
59	        ("line_number_count", ctypes.c_uint16),
60	        ("flags", ctypes.c_uint32),
61	    ]
62	
63	
64	class CoffSymbol(ctypes.LittleEndianStructure):
65	    _pack_ = True
66	    _fields_ = [
67	        ("name", CoffName),
68	        ("value", ctypes.c_uint32),
69	        ("section_number", ctypes.c_int16),
70	        ("type", ctypes.c_uint16),
71	        ("storage_class", ctypes.c_uint8),
72	        ("auxiliary_count", ctypes.c_uint8),
73	    ]
74	
75	
76	class Symbol:
77	    def __init__(self, image, symbol: CoffSymbol):
78	        self._image = image
79	        self._coff = symbol
80	
81	    @property
82	    def name(self):
83	        if self._coff.name.reference.zeroes:
84	            return decode_asciiz(bytes(self._coff.name.immediate))
85	
86	        offset = self._coff.name.reference.offset
87	        offset -= ctypes.sizeof(ctypes.c_uint32)
88	        return self._image.get_string(offset)
89	
90	    def get_value(self, offset):
91	        section_number = self._coff.section_number
92	
93	        if section_number == COFF_SN_UNDEFINED:
94	            return None
95	
96	        if section_number == COFF_SN_DEBUG:
97	            return None
98	
99	        if section_number == COFF_SN_ABSOLUTE:
100	            return bytes(ctypes.c_uint32(self._coff.value))
101	
102	        section_data = self._image.get_section_data(section_number)
103	        section_offset = self._coff.value + offset
104	        return section_data[section_offset:]
105	
106	
107	class Image:
108	    def __init__(self, data):
109	        header = CoffFileHeader.from_buffer_copy(data)
110	        header_size = ctypes.sizeof(header) + header.optional_header_size
111	
112	        sections_desc = CoffSection * header.section_count
113	        sections = sections_desc.from_buffer_copy(data, header_size)
114	
115	        symbols_desc = CoffSymbol * header.symbol_count
116	        symbols = symbols_desc.from_buffer_copy(data, header.symbol_table_offset)
117	
118	        strings_offset = header.symbol_table_offset + ctypes.sizeof(symbols)
119	        strings = Image._parse_strings(data[strings_offset:])
120	
121	        self._data = data
122	        self._header = header
123	        self._sections = sections
124	        self._symbols = symbols
125	        self._strings = strings
126	
127	    @staticmethod
128	    def _parse_strings(data):
129	        full_size = ctypes.c_uint32.from_buffer_copy(data)
130	        header_size = ctypes.sizeof(full_size)
131	        return data[header_size : full_size.value]
132	
133	    @property
134	    def symbols(self):
135	        i = 0
136	        while i < self._header.symbol_count:
137	            symbol = self._symbols[i]
138	            yield Symbol(self, symbol)
139	            i += symbol.auxiliary_count + 1
140	
141	    def get_section_data(self, number):
142	        # section numbers are 1-based
143	        section = self._sections[number - 1]
144	        base = section.data_offset
145	        return self._data[base : base + section.size]
146	
147	    def get_string(self, offset):
148	        return decode_asciiz(self._strings[offset:])
149	
150	
151	def decode_asciiz(data):
152	    index = data.find(b'\x00')
153	    end = index if index >= 0 else len(data)
154	    return data[:end].decode()
```

**`dpdk/lib/eal/common/eal_trace.h`** — trace(struct)

```c
1	/* SPDX-License-Identifier: BSD-3-Clause
2	 * Copyright(C) 2020 Marvell International Ltd.
3	 */
4	
5	#ifndef __EAL_TRACE_H
6	#define __EAL_TRACE_H
7	
8	#include <rte_cycles.h>
9	#include <rte_log.h>
10	#include <rte_malloc.h>
11	#include <rte_spinlock.h>
12	#include <rte_trace.h>
13	#include <rte_trace_point.h>
14	#include <rte_uuid.h>
15	
16	#include "eal_private.h"
17	#include "eal_thread.h"
18	
19	#define trace_err(...) \
20		RTE_LOG_LINE_PREFIX(ERR, EAL, "%s():%u ", __func__ RTE_LOG_COMMA __LINE__, __VA_ARGS__)
21	
22	#define trace_crit(...) \
23		RTE_LOG_LINE_PREFIX(CRIT, EAL, "%s():%u ", __func__ RTE_LOG_COMMA __LINE__, __VA_ARGS__)
24	
25	#define TRACE_CTF_MAGIC 0xC1FC1FC1
26	#define TRACE_MAX_ARGS	32
27	
28	struct trace_point {
29		STAILQ_ENTRY(trace_point) next;
30		rte_trace_point_t *handle;
31		const char *name;
32		char *ctf_field;
33	};
34	
35	enum trace_area_e {
36		TRACE_AREA_HEAP,
37		TRACE_AREA_HUGEPAGE,
38	};
39	
40	struct thread_mem_meta {
41		void *mem;
42		enum trace_area_e area;
43	};
44	
45	struct trace_arg {
46		STAILQ_ENTRY(trace_arg) next;
47		char *val;
48	};
49	
50	struct trace {
51		char *dir;
52		int register_errno;
53		RTE_ATOMIC(uint32_t) status;
54		enum rte_trace_mode mode;
55		rte_uuid_t uuid;
56		uint32_t buff_len;
57		STAILQ_HEAD(, trace_arg) args;
58		uint32_t nb_trace_points;
59		uint32_t nb_trace_mem_list;
60		struct thread_mem_meta *lcore_meta;
61		uint64_t epoch_sec;
62		uint64_t epoch_nsec;
63		uint64_t uptime_ticks;
64		char *ctf_meta;
65		uint32_t ctf_meta_offset_freq;
66		uint32_t ctf_meta_offset_freq_off_s;
67		uint32_t ctf_meta_offset_freq_off;
68		RTE_ATOMIC(uint16_t) ctf_fixup_done;
69		rte_spinlock_t lock;
70	};
71	
72	/* Helper functions */
73	static inline uint16_t
74	trace_id_get(rte_trace_point_t *trace)
75	{
76		return (*trace & __RTE_TRACE_FIELD_ID_MASK) >>
77			__RTE_TRACE_FIELD_ID_SHIFT;
78	}
79	
80	static inline size_t
81	trace_mem_sz(uint32_t len)
82	{
83		return len + sizeof(struct __rte_trace_header);
84	}
85	
86	/* Trace object functions */
87	struct trace *trace_obj_get(void);
88	
89	/* Trace point list functions */
90	STAILQ_HEAD(trace_point_head, trace_point);
91	struct trace_point_head *trace_list_head_get(void);
92	
93	/* Util functions */
94	const char *trace_mode_to_string(enum rte_trace_mode mode);
95	const char *trace_area_to_string(enum trace_area_e area);
96	int trace_args_apply(const char *arg);
97	void trace_bufsz_args_apply(void);
98	bool trace_has_duplicate_entry(void);
99	void trace_uuid_generate(void);
100	int trace_metadata_create(void);
101	void trace_metadata_destroy(void);
102	char *trace_metadata_fixup_field(const char *field);
103	int trace_epoch_time_save(void);
104	void trace_mem_free(void);
105	void trace_mem_per_thread_free(void);
106	
107	/* EAL interface */
108	int eal_trace_init(void);
109	void eal_trace_fini(void);
110	int eal_trace_args_save(const char *val);
111	void eal_trace_args_free(void);
112	int eal_trace_dir_args_save(const char *val);
113	int eal_trace_mode_args_save(const char *val);
114	int eal_trace_bufsz_args_save(const char *val);
115	
116	#endif /* __EAL_TRACE_H */
```

**`dpdk/lib/eal/common/eal_common_trace.c`** — trace(variable)

```c
21	static RTE_DEFINE_PER_LCORE(char *, ctf_field);
22	
23	static struct trace_point_head tp_list = STAILQ_HEAD_INITIALIZER(tp_list);
24	static struct trace trace = { .args = STAILQ_HEAD_INITIALIZER(trace.args), };
25	
26	struct trace *
27	trace_obj_get(void)
```

**`dpdk/examples/vm_power_manager/channel_manager.h`** — libvirt_vm_info(struct)

```cpp
31	#define MAX_VCPUS 20
32	
33	
34	struct libvirt_vm_info {
35		const char *vm_name;
36		unsigned int pcpus[MAX_VCPUS];
37		uint8_t num_cpus;
38	};
39	
40	extern struct libvirt_vm_info lvm_info[MAX_CLIENTS];
41	/* Communication Channel Status */
```

**`freebsd/contrib/zstd/lib/decompress/zstd_decompress_block.c`** — calls(calls), symbolEncodingType_e(calls), ZSTD_buildSeqTable(calls), ZSTD_isError(calls), ZSTD_buildSeqTable(function), ZSTD_decodeSeqHeaders(function), MEM_readLE16(calls)

```c
526	/*! ZSTD_buildSeqTable() :
527	 * @return : nb bytes read from src,
528	 *           or an error code if it fails */
529	static size_t ZSTD_buildSeqTable(ZSTD_seqSymbol* DTableSpace, const ZSTD_seqSymbol** DTablePtr,
530	                                 symbolEncodingType_e type, unsigned max, U32 maxLog,
531	                                 const void* src, size_t srcSize,
532	                                 const U32* baseValue, const U32* nbAdditionalBits,
533	                                 const ZSTD_seqSymbol* defaultTable, U32 flagRepeatTable,
534	                                 int ddictIsCold, int nbSeq, U32* wksp, size_t wkspSize,
535	                                 int bmi2)
536	{
537	    switch(type)
538	    {
539	    case set_rle :
540	        RETURN_ERROR_IF(!srcSize, srcSize_wrong, "");
541	        RETURN_ERROR_IF((*(const BYTE*)src) > max, corruption_detected, "");
542	        {   U32 const symbol = *(const BYTE*)src;
543	            U32 const baseline = baseValue[symbol];
544	            U32 const nbBits = nbAdditionalBits[symbol];
545	            ZSTD_buildSeqTable_rle(DTableSpace, baseline, nbBits);
546	        }
547	        *DTablePtr = DTableSpace;
548	        return 1;
549	    case set_basic :
550	        *DTablePtr = defaultTable;
551	        return 0;
552	    case set_repeat:
553	        RETURN_ERROR_IF(!flagRepeatTable, corruption_detected, "");
554	        /* prefetch FSE table if used */
555	        if (ddictIsCold && (nbSeq > 24 /* heuristic */)) {
556	            const void* const pStart = *DTablePtr;
557	            size_t const pSize = sizeof(ZSTD_seqSymbol) * (SEQSYMBOL_TABLE_SIZE(maxLog));
558	            PREFETCH_AREA(pStart, pSize);
559	        }
560	        return 0;
561	    case set_compressed :
562	        {   unsigned tableLog;
563	            S16 norm[MaxSeq+1];
564	            size_t const headerSize = FSE_readNCount(norm, &max, &tableLog, src, srcSize);
565	            RETURN_ERROR_IF(FSE_isError(headerSize), corruption_detected, "");
566	            RETURN_ERROR_IF(tableLog > maxLog, corruption_detected, "");
567	            ZSTD_buildFSETable(DTableSpace, norm, max, baseValue, nbAdditionalBits, tableLog, wksp, wkspSize, bmi2);
568	            *DTablePtr = DTableSpace;
569	            return headerSize;
570	        }
571	    default :
572	        assert(0);
573	        RETURN_ERROR(GENERIC, "impossible");
574	    }
575	}
576	
577	size_t ZSTD_decodeSeqHeaders(ZSTD_DCtx* dctx, int* nbSeqPtr,
578	                             const void* src, size_t srcSize)
579	{
580	    const BYTE* const istart = (const BYTE* const)src;
581	    const BYTE* const iend = istart + srcSize;
582	    const BYTE* ip = istart;
583	    int nbSeq;
584	    DEBUGLOG(5, "ZSTD_decodeSeqHeaders");
585	
586	    /* check */
587	    RETURN_ERROR_IF(srcSize < MIN_SEQUENCES_SIZE, srcSize_wrong, "");
588	
589	    /* SeqHead */
590	    nbSeq = *ip++;
591	    if (!nbSeq) {
592	        *nbSeqPtr=0;
593	        RETURN_ERROR_IF(srcSize != 1, srcSize_wrong, "");
594	        return 1;
595	    }
596	    if (nbSeq > 0x7F) {
597	        if (nbSeq == 0xFF) {
598	            RETURN_ERROR_IF(ip+2 > iend, srcSize_wrong, "");
599	            nbSeq = MEM_readLE16(ip) + LONGNBSEQ;
600	            ip+=2;
601	        } else {
602	            RETURN_ERROR_IF(ip >= iend, srcSize_wrong, "");
603	            nbSeq = ((nbSeq-0x80)<<8) + *ip++;
604	        }
605	    }
606	    *nbSeqPtr = nbSeq;
607	
608	    /* FSE table descriptors */
609	    RETURN_ERROR_IF(ip+1 > iend, srcSize_wrong, ""); /* minimum possible size: 1 byte for symbol encoding types */
610	    {   symbolEncodingType_e const LLtype = (symbolEncodingType_e)(*ip >> 6);
611	        symbolEncodingType_e const OFtype = (symbolEncodingType_e)((*ip >> 4) & 3);
612	        symbolEncodingType_e const MLtype = (symbolEncodingType_e)((*ip >> 2) & 3);
613	        ip++;
614	
615	        /* Build DTables */
616	        {   size_t const llhSize = ZSTD_buildSeqTable(dctx->entropy.LLTable, &dctx->LLTptr,
617	                                                      LLtype, MaxLL, LLFSELog,
618	                                                      ip, iend-ip,
619	                                                      LL_base, LL_bits,
620	                                                      LL_defaultDTable, dctx->fseEntropy,
621	                                                      dctx->ddictIsCold, nbSeq,
622	                                                      dctx->workspace, sizeof(dctx->workspace),
623	                                                      dctx->bmi2);
624	            RETURN_ERROR_IF(ZSTD_isError(llhSize), corruption_detected, "ZSTD_buildSeqTable failed");
625	            ip += llhSize;
626	        }
627	
628	        {   size_t const ofhSize = ZSTD_buildSeqTable(dctx->entropy.OFTable, &dctx->OFTptr,
629	                                                      OFtype, MaxOff, OffFSELog,
630	                                                      ip, iend-ip,
631	                                                      OF_base, OF_bits,
632	                                                      OF_defaultDTable, dctx->fseEntropy,
633	                                                      dctx->ddictIsCold, nbSeq,
634	                                                      dctx->workspace, sizeof(dctx->workspace),
635	                                                      dctx->bmi2);
636	            RETURN_ERROR_IF(ZSTD_isError(ofhSize), corruption_detected, "ZSTD_buildSeqTable failed");
637	            ip += ofhSize;
638	        }
639	
640	        {   size_t const mlhSize = ZSTD_buildSeqTable(dctx->entropy.MLTable, &dctx->MLTptr,
641	                                                      MLtype, MaxML, MLFSELog,
642	                                                      ip, iend-ip,
643	                                                      ML_base, ML_bits,
644	                                                      ML_defaultDTable, dctx->fseEntropy,
645	                                                      dctx->ddictIsCold, nbSeq,
646	                                                      dctx->workspace, sizeof(dctx->workspace),
647	                                                      dctx->bmi2);
648	            RETURN_ERROR_IF(ZSTD_isError(mlhSize), corruption_detected, "ZSTD_buildSeqTable failed");
649	            ip += mlhSize;
650	        }
651	    }
652	
653	    return ip-istart;
654	}
655	
656	
657	typedef struct {
```

**`freebsd/netgraph/ng_etf.c`** — filter(struct)

```c
130		hook_p  hook;
131	};
132	
133	struct filter {
134		LIST_ENTRY(filter) next;
135		u_int16_t	ethertype;	/* network order ethertype */
136		hook_p		match_hook;	/* Hook to use on a match */
137	};
138	
139	#define HASHSIZE 16 /* Dont change this without changing HASH() */
140	#define HASH(et) ((((et)>>12)+((et)>>8)+((et)>>4)+(et)) & 0x0f)
```

**`freebsd/contrib/zstd/lib/common/zstd_internal.h`** — symbolEncodingType_e(enum)

```c
168	#define MIN_CBLOCK_SIZE (1 /*litCSize*/ + 1 /* RLE or RAW */ + MIN_SEQUENCES_SIZE /* nbSeq==0 */)   /* for a non-null block */
169	
170	#define HufLog 12
171	typedef enum { set_basic, set_rle, set_compressed, set_repeat } symbolEncodingType_e;
172	
173	#define LONGNBSEQ 0x7F00
174	
```

**Not shown above — explore these names for their source**

- freebsd/netpfil/pf/pf_table.c: pfr_pool_get:2292, pfr_ktable_select_active:2468, pfr_kentry_byidx:2416, pfr_prepare_network:934, pfr_sockaddr_to_pf_addr:1075, pfr_ffaddr:120
- dpdk/lib/net/rte_ether.h: rte_is_multicast_ether_addr:153
- freebsd/contrib/ngatm/netnatm/sig/sig_uni.c: uni_undel:557
- freebsd/contrib/zstd/lib/common/mem.h: MEM_readLE32:320, MEM_readLE16:288, MEM_readLE24:309, MEM_isLittleEndian:156, MEM_read32:212, MEM_swap32:244, MEM_readLEST:352
- lib/ff_dpdk_kni.c: ff_kni_proto_filter:370
- dpdk/drivers/net/hns3/hns3_ethdev.c: hns3_add_mc_mac_addr:1776, hns3_remove_mc_mac_addr:1825
- dpdk/drivers/net/virtio/virtio_ethdev.c: virtio_mac_addr_add:889, virtio_mac_addr_remove:924
- freebsd/contrib/zstd/lib/common/entropy_common.c: HUF_isError:34, FSE_readNCount_body:63
- freebsd/contrib/zstd/lib/compress/zstd_compress.c: ZSTD_loadCEntropy:3167, ZSTD_loadZstdDictionary:3268
- freebsd/net/pfvar.h: pfr_kstate_counter_add:1535, pf_addrcpy:576
- ... and 19 more files

---
> **Complete source for 8 files is included above — do NOT re-read them.** If your question also needs files/symbols listed under "Not shown above" (or any area this call didn't cover), make ANOTHER codegraph_explore targeting those names — it returns the same source with line numbers and is cheaper and more complete than reading. Reserve Read for a single specific line range explore can't surface.

> **Explore budget: 3 calls for this project (14,182 files indexed).** Each call covers ~6 files; if your question spans more, spend your remaining calls on the uncovered area BEFORE falling back to Read — another explore is cheaper and more complete than reading those files. Synthesize once you've used 3.

## finding-9139b7ab6bf4 — 固定上限 nd6_maxndopt=10 会提前终止集合处理

Query: `Trace the implementation and all relevant callers for 固定上限 nd6_maxndopt=10 会提前终止集合处理. Start from freebsd/netinet6/nd6.c symbol nd6_options. Look specifically for an alternative implementation or counterevidence that would make the suspected design-to-code difference invalid.`

**Dynamic-dispatch links among your symbols**
(synthesized — the indirect hops grep/Read would reconstruct; the `@file:line` is the wiring site)

- ng_generic_msg → ngs_rcvmsg   [dynamic: fn-pointer ng_type.rcvmsg @freebsd/netgraph/ng_base.c:2934]

> Full source for these symbols is below — the call flow among them, followed by their bodies.
**Exploration: Trace the implementation and all relevant callers for 固定上限 nd6_maxndopt=10 会提前终止集合处理. Start from freebsd/netinet6/nd6.c symbol nd6_options. Look specifically for an alternative implementation or counterevidence that would make the suspected design-to-code difference invalid.**

Found 25 symbols across 3 files.

**Blast radius — what depends on these (update/verify before editing)**

- `nd6_options` (freebsd/netinet6/nd6.c:452) — 5 callers in `freebsd/netinet6/icmp6.c`, `freebsd/netinet6/nd6_nbr.c`, `freebsd/netinet6/nd6_rtr.c`; ⚠️ no covering tests found
- `nd6_option` (freebsd/netinet6/nd6.c:402) — 1 caller in `freebsd/netinet6/nd6.c`; ⚠️ no covering tests found
- `make` (freebsd/contrib/libsodium/packaging/dotnet-core/prepare.py:67) — 1 caller in `freebsd/contrib/libsodium/packaging/dotnet-core/prepare.py`; ⚠️ no covering tests found

**Relationships**

**calls:**
- nd6_options → nd6_option
- icmp6_redirect_input → nd6_options
- nd6_ns_input → nd6_options
- nd6_na_input → nd6_options
- nd6_rs_input → nd6_options
- nd6_ra_input → nd6_options
- icmp6_redirect_input → m_pullup
- icmp6_redirect_input → in6_setscope
- icmp6_redirect_input → ip6_sprintf
- icmp6_redirect_input → in6_splitscope
- icmp6_redirect_input → fib6_lookup
- icmp6_redirect_input → icmp6_redirect_diag
- icmp6_redirect_input → nd6_option_init
- icmp6_redirect_input → nd6_cache_lladdr
- icmp6_redirect_input → rib_add_redirect
- ... and 65 more

**instantiates:**
- main → WindowsItem
- main → Version
- main → MacOSItem
- main → LinuxItem
- main → ExtraItem

**references:**
- main → MAKEFILE
- main → DOCKER
- main → PROPSFILE
- main → EXTRAS
- main → LINUX
- main → MACOS
- main → WINDOWS
- __init__ → LIBRARY
- __init__ → CACHEDIR
- __init__ → LIBRARY
- __init__ → CACHEDIR
- make → DOCKER
- __init__ → LIBRARY
- __init__ → CACHEDIR
- __init__ → CACHEDIR

**Source Code**

> The code below is the **verbatim, current on-disk source** of these files — re-read from disk on this call and line-numbered, byte-for-byte identical to what the Read tool returns. It is NOT a summary, outline, or stale cache. Treat each block as a Read you have already performed: do not Read a file shown here.

**`freebsd/contrib/libsodium/src/libsodium/randombytes/randombytes.c`** — implementation(constant)

```c
1	
2	#include <assert.h>
3	#include <limits.h>
4	#include <stdint.h>
5	#include <stdlib.h>
6	
7	#include <sys/types.h>
8	
9	#ifdef __EMSCRIPTEN__
10	# include <emscripten.h>
11	#endif
12	
13	#include "core.h"
14	#include "crypto_stream_chacha20.h"
15	#include "randombytes.h"
16	#ifdef RANDOMBYTES_DEFAULT_IMPLEMENTATION
17	# include "randombytes_default.h"
18	#else
19	# ifdef __native_client__
20	#  include "randombytes_nativeclient.h"
21	# else
22	#  include "randombytes_sysrandom.h"
23	# endif
24	#endif
25	#include "private/common.h"
26	
27	/* C++Builder defines a "random" macro */
28	#undef random
29	
30	static const randombytes_implementation *implementation;
31	
32	#ifndef RANDOMBYTES_DEFAULT_IMPLEMENTATION
33	# ifdef __EMSCRIPTEN__
34	#  define RANDOMBYTES_DEFAULT_IMPLEMENTATION NULL
35	# else
36	#  ifdef __native_client__
37	#   define RANDOMBYTES_DEFAULT_IMPLEMENTATION &randombytes_nativeclient_implementation;
38	#  else
39	#   define RANDOMBYTES_DEFAULT_IMPLEMENTATION &randombytes_sysrandom_implementation;
40	#  endif
41	# endif
42	#endif
43	
44	static void
45	randombytes_init_if_needed(void)
46	{
47	    if (implementation == NULL) {
48	        implementation = RANDOMBYTES_DEFAULT_IMPLEMENTATION;
49	        randombytes_stir();
50	    }
51	}
52	
53	int
54	randombytes_set_implementation(randombytes_implementation *impl)
55	{
56	    implementation = impl;
57	
58	    return 0;
59	}
60	
61	const char *
62	randombytes_implementation_name(void)
63	{
64	#ifndef __EMSCRIPTEN__
65	    randombytes_init_if_needed();
66	    return implementation->implementation_name();
67	#else
68	    return "js";
69	#endif
70	}
71	
72	uint32_t
73	randombytes_random(void)
74	{
75	#ifndef __EMSCRIPTEN__
76	    randombytes_init_if_needed();
77	    return implementation->random();
78	#else
79	    return EM_ASM_INT_V({
80	        return Module.getRandomValue();
81	    });
82	#endif
83	}
84	
85	void
86	randombytes_stir(void)
87	{
88	#ifndef __EMSCRIPTEN__
89	    randombytes_init_if_needed();
90	    if (implementation->stir != NULL) {
91	        implementation->stir();
92	    }
93	#else
94	    EM_ASM({
95	        if (Module.getRandomValue === undefined) {
96	            try {
97	                var window_ = 'object' === typeof window ? window : self;
98	                var crypto_ = typeof window_.crypto !== 'undefined' ? window_.crypto : window_.msCrypto;
99	                var randomValuesStandard = function() {
100	                    var buf = new Uint32Array(1);
101	                    crypto_.getRandomValues(buf);
102	                    return buf[0] >>> 0;
103	                };
104	                randomValuesStandard();
105	                Module.getRandomValue = randomValuesStandard;
106	            } catch (e) {
107	                try {
108	                    var crypto = require('crypto');
109	                    var randomValueNodeJS = function() {
110	                        var buf = crypto['randomBytes'](4);
111	                        return (buf[0] << 24 | buf[1] << 16 | buf[2] << 8 | buf[3]) >>> 0;
112	                    };
113	                    randomValueNodeJS();
114	                    Module.getRandomValue = randomValueNodeJS;
115	                } catch (e) {
116	                    throw 'No secure random number generator found';
117	                }
118	            }
119	        }
120	    });
121	#endif
122	}
123	
124	uint32_t
125	randombytes_uniform(const uint32_t upper_bound)
126	{
127	    uint32_t min;
128	    uint32_t r;
129	
130	#ifndef __EMSCRIPTEN__
131	    randombytes_init_if_needed();
132	    if (implementation->uniform != NULL) {
133	        return implementation->uniform(upper_bound);
134	    }
135	#endif
136	    if (upper_bound < 2) {
137	        return 0;
138	    }
139	    min = (1U + ~upper_bound) % upper_bound; /* = 2**32 mod upper_bound */
140	    do {
141	        r = randombytes_random();
142	    } while (r < min);
143	    /* r is now clamped to a set whose size mod upper_bound == 0
144	     * the worst case (2**31+1) requires ~ 2 attempts */
145	
146	    return r % upper_bound;
147	}
148	
149	void
150	randombytes_buf(void * const buf, const size_t size)
151	{
152	#ifndef __EMSCRIPTEN__
153	    randombytes_init_if_needed();
154	    if (size > (size_t) 0U) {
155	        implementation->buf(buf, size);
156	    }
157	#else
158	    unsigned char *p = (unsigned char *) buf;
159	    size_t         i;
160	
161	    for (i = (size_t) 0U; i < size; i++) {
162	        p[i] = (unsigned char) randombytes_random();
163	    }
164	#endif
165	}
166	
167	void
168	randombytes_buf_deterministic(void * const buf, const size_t size,
169	                              const unsigned char seed[randombytes_SEEDBYTES])
170	{
171	    static const unsigned char nonce[crypto_stream_chacha20_ietf_NONCEBYTES] = {
172	        'L', 'i', 'b', 's', 'o', 'd', 'i', 'u', 'm', 'D', 'R', 'G'
173	    };
174	
175	    COMPILER_ASSERT(randombytes_SEEDBYTES == crypto_stream_chacha20_ietf_KEYBYTES);
176	#if SIZE_MAX > 0x4000000000ULL
177	    COMPILER_ASSERT(randombytes_BYTES_MAX <= 0x4000000000ULL);
178	    if (size > 0x4000000000ULL) {
179	        sodium_misuse();
180	    }
181	#endif
182	    crypto_stream_chacha20_ietf((unsigned char *) buf, (unsigned long long) size,
183	                                nonce, seed);
184	}
185	
186	size_t
187	randombytes_seedbytes(void)
188	{
189	    return randombytes_SEEDBYTES;
190	}
191	
192	int
193	randombytes_close(void)
194	{
195	    if (implementation != NULL && implementation->close != NULL) {
196	        return implementation->close();
197	    }
198	    return 0;
199	}
200	
201	void
202	randombytes(unsigned char * const buf, const unsigned long long buf_len)
203	{
204	    assert(buf_len <= SIZE_MAX);
205	    randombytes_buf(buf, (size_t) buf_len);
206	}
```

**`freebsd/contrib/libsodium/packaging/dotnet-core/prepare.py`** — make(method), WindowsItem(class), main(function), __init__(method), Version(class), MacOSItem(class), LinuxItem(class), ExtraItem(class), MAKEFILE(variable), DOCKER(variable), PROPSFILE(variable), EXTRAS(variable), LINUX(variable), MACOS(variable), WINDOWS(variable), +2 more

```python
1	#!/usr/bin/env python3
2	
3	import os.path
4	import re
5	import sys
6	
7	WINDOWS = [
8	  # --------------------- ----------------- #
9	  # Runtime ID            Platform          #
10	  # --------------------- ----------------- #
11	  ( 'win-x64',            'x64'             ),
12	  ( 'win-x86',            'Win32'           ),
13	  # --------------------- ----------------- #
14	]
15	
16	MACOS = [
17	  # --------------------- ----------------- #
18	  # Runtime ID            Codename          #
19	  # --------------------- ----------------- #
20	  ( 'osx-x64',            'sierra'          ),
21	  # --------------------- ----------------- #
22	]
23	
24	LINUX = [
25	  # --------------------- ----------------- #
26	  # Runtime ID            Docker Image      #
27	  # --------------------- ----------------- #
28	  ( 'linux-x64',          'debian:stretch'  ),
29	  # --------------------- ----------------- #
30	]
31	
32	EXTRAS = [ 'LICENSE', 'AUTHORS', 'ChangeLog' ]
33	
34	PROPSFILE = 'libsodium.props'
35	MAKEFILE = 'Makefile'
36	BUILDDIR = 'build'
37	CACHEDIR = 'cache'
38	TEMPDIR = 'temp'
39	
40	PACKAGE = 'libsodium'
41	LIBRARY = 'libsodium'
42	
43	DOCKER = 'sudo docker'
44	
45	class Version:
46	
47	  def __init__(self, libsodium_version, package_version):
48	    self.libsodium_version = libsodium_version
49	    self.package_version = package_version
50	
51	    self.builddir = os.path.join(BUILDDIR, libsodium_version)
52	    self.tempdir = os.path.join(TEMPDIR, libsodium_version)
53	    self.projfile = os.path.join(self.builddir, '{0}.{1}.pkgproj'.format(PACKAGE, package_version))
54	    self.propsfile = os.path.join(self.builddir, '{0}.props'.format(PACKAGE))
55	    self.pkgfile = os.path.join(BUILDDIR, '{0}.{1}.nupkg'.format(PACKAGE, package_version))
56	
57	class WindowsItem:
58	
59	  def __init__(self, version, rid, platform):
60	    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}-msvc.zip'.format(version.libsodium_version)
61	    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
62	    self.packfile = os.path.join(version.builddir, 'runtimes', rid, 'native', LIBRARY + '.dll')
63	    self.itemfile = '{0}/Release/v140/dynamic/libsodium.dll'.format(platform)
64	    self.tempdir = os.path.join(version.tempdir, rid)
65	    self.tempfile = os.path.join(self.tempdir, os.path.normpath(self.itemfile))
66	
67	  def make(self, f):
68	    f.write('\n')
69	    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
70	    f.write('\t@mkdir -p $(dir $@)\n')
71	    f.write('\tcp -f $< $@\n')
72	    f.write('\n')
73	    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
74	    f.write('\t@mkdir -p $(dir $@)\n')
75	    f.write('\tcd {0} && unzip -q -DD -o {1} \'{2}\'\n'.format(
76	      self.tempdir,
77	      os.path.relpath(self.cachefile, self.tempdir),
78	      self.itemfile
79	    ))
80	
81	class MacOSItem:
82	
83	  def __init__(self, version, rid, codename):
84	    self.url = 'https://bintray.com/homebrew/bottles/download_file?file_path=libsodium-{0}.{1}.bottle.tar.gz'.format(version.libsodium_version, codename)
85	    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
86	    self.packfile = os.path.join(version.builddir, 'runtimes', rid, 'native', LIBRARY + '.dylib')
87	    self.itemfile = 'libsodium/{0}/lib/libsodium.dylib'.format(version.libsodium_version)
88	    self.tempdir = os.path.join(version.tempdir, rid)
89	    self.tempfile = os.path.join(self.tempdir, os.path.normpath(self.itemfile))
90	
91	  def make(self, f):
92	    f.write('\n')
93	    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
94	    f.write('\t@mkdir -p $(dir $@)\n')
95	    f.write('\tcp -f $< $@\n')
96	    f.write('\n')
97	    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
98	    f.write('\t@mkdir -p $(dir $@)\n')
99	    f.write('\tcd {0} && tar xzmf {1} \'{2}\'\n'.format(
100	      self.tempdir,
101	      os.path.relpath(self.cachefile, self.tempdir),
102	      os.path.dirname(self.itemfile)
103	    ))
104	
105	class LinuxItem:
106	
107	  def __init__(self, version, rid, docker_image):
108	    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}.tar.gz'.format(version.libsodium_version)
109	    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
110	    self.packfile = os.path.join(version.builddir, 'runtimes', rid, 'native', LIBRARY + '.so')
111	    self.tempdir = os.path.join(version.tempdir, rid)
112	    self.tempfile = os.path.join(self.tempdir, 'libsodium.so')
113	    self.docker_image = docker_image
114	    self.recipe = rid
115	
116	  def make(self, f):
117	    recipe = self.recipe
118	    while not os.path.exists(os.path.join('recipes', recipe)):
119	      m = re.fullmatch(r'([^.-]+)((([.][^.-]+)*)[.][^.-]+)?([-].*)?', recipe)
120	      if m.group(5) is None:
121	        recipe = 'build'
122	        break
123	      elif m.group(2) is None:
124	        recipe = m.group(1)
125	      else:
126	        recipe = m.group(1) + m.group(3) + m.group(5)
127	
128	    f.write('\n')
129	    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
130	    f.write('\t@mkdir -p $(dir $@)\n')
131	    f.write('\tcp -f $< $@\n')
132	    f.write('\n')
133	    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
134	    f.write('\t@mkdir -p $(dir $@)\n')
135	    f.write('\t{0} run --rm '.format(DOCKER) +
136	            '-v $(abspath recipes):/io/recipes ' +
137	            '-v $(abspath $<):/io/libsodium.tar.gz ' +
138	            '-v $(abspath $(dir $@)):/io/output ' +
139	            '{0} sh -x -e /io/recipes/{1}\n'.format(self.docker_image, recipe))
140	
141	class ExtraItem:
142	
143	  def __init__(self, version, filename):
144	    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}.tar.gz'.format(version.libsodium_version)
145	    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
146	    self.packfile = os.path.join(version.builddir, filename)
147	    self.itemfile = 'libsodium-{0}/{1}'.format(version.libsodium_version, filename)
148	    self.tempdir = os.path.join(version.tempdir, 'extras')
149	    self.tempfile = os.path.join(self.tempdir, os.path.normpath(self.itemfile))
150	
151	  def make(self, f):
152	    f.write('\n')
153	    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
154	    f.write('\t@mkdir -p $(dir $@)\n')
155	    f.write('\tcp -f $< $@\n')
156	    f.write('\n')
157	    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
158	    f.write('\t@mkdir -p $(dir $@)\n')
159	    f.write('\tcd {0} && tar xzmf {1} \'{2}\'\n'.format(
160	      self.tempdir,
161	      os.path.relpath(self.cachefile, self.tempdir),
162	      self.itemfile
163	    ))
164	
165	def main(args):
166	  m = re.fullmatch(r'((\d+\.\d+\.\d+)(\.\d+)?)(?:-(\w+(?:[_.-]\w+)*))?', args[1]) if len(args) == 2 else None
167	
168	  if m is None:
169	    print('Usage:')
170	    print('       python3 prepare.py <version>')
171	    print()
172	    print('Examples:')
173	    print('       python3 prepare.py 1.0.16-preview-01')
174	    print('       python3 prepare.py 1.0.16-preview-02')
175	    print('       python3 prepare.py 1.0.16-preview-03')
176	    print('       python3 prepare.py 1.0.16')
177	    print('       python3 prepare.py 1.0.16.1-preview-01')
178	    print('       python3 prepare.py 1.0.16.1')
179	    print('       python3 prepare.py 1.0.16.2')
180	    return 1
181	
182	  version = Version(m.group(2), m.group(0))
183	
184	  items = [ WindowsItem(version, rid, platform)   for (rid, platform) in WINDOWS   ] + \
185	          [ MacOSItem(version, rid, codename)     for (rid, codename) in MACOS     ] + \
186	          [ LinuxItem(version, rid, docker_image) for (rid, docker_image) in LINUX ] + \
187	          [ ExtraItem(version, filename)          for filename in EXTRAS           ]
188	
189	  downloads = {item.cachefile: item.url for item in items}
190	
191	  with open(MAKEFILE, 'w') as f:
192	    f.write('all: {0}\n'.format(version.pkgfile))
193	
194	    for download in sorted(downloads):
195	      f.write('\n')
196	      f.write('{0}:\n'.format(download))
197	      f.write('\t@mkdir -p $(dir $@)\n')
198	      f.write('\tcurl -f#Lo $@ \'{0}\'\n'.format(downloads[download]))
199	
200	    for item in items:
201	      item.make(f)
202	
203	    f.write('\n')
204	    f.write('{0}: {1}\n'.format(version.propsfile, PROPSFILE))
205	    f.write('\t@mkdir -p $(dir $@)\n')
206	    f.write('\tcp -f $< $@\n')
207	
208	    f.write('\n')
209	    f.write('{0}: {1}\n'.format(version.projfile, version.propsfile))
210	    f.write('\t@mkdir -p $(dir $@)\n')
211	    f.write('\techo \'' +
212	            '<Project Sdk="Microsoft.NET.Sdk">' +
213	            '<Import Project="{0}" />'.format(os.path.relpath(version.propsfile, os.path.dirname(version.projfile))) +
214	            '<PropertyGroup>' +
215	            '<Version>{0}</Version>'.format(version.package_version) +
216	            '</PropertyGroup>' +
217	            '</Project>\' > $@\n')
218	
219	    f.write('\n')
220	    f.write('{0}:'.format(version.pkgfile))
221	    f.write(' \\\n\t\t{0}'.format(version.projfile))
222	    f.write(' \\\n\t\t{0}'.format(version.propsfile))
223	    for item in items:
224	      f.write(' \\\n\t\t{0}'.format(item.packfile))
225	    f.write('\n')
226	    f.write('\t@mkdir -p $(dir $@)\n')
227	    f.write('\t{0} run --rm '.format(DOCKER) +
228	            '-v $(abspath recipes):/io/recipes ' +
229	            '-v $(abspath $(dir $<)):/io/input ' +
230	            '-v $(abspath $(dir $@)):/io/output ' +
231	            '{0} sh -x -e /io/recipes/{1} {2}\n'.format('microsoft/dotnet:2.0-sdk', 'pack', os.path.relpath(version.projfile, version.builddir)))
232	
233	    f.write('\n')
234	    f.write('test: {0}\n'.format(version.pkgfile))
235	    f.write('\t{0} run --rm '.format(DOCKER) +
236	            '-v $(abspath recipes):/io/recipes ' +
237	            '-v $(abspath $(dir $<)):/io/packages ' +
238	            '{0} sh -x -e /io/recipes/{1} "{2}"\n'.format('microsoft/dotnet:2.0-sdk', 'test', version.package_version))
239	
240	  print('prepared', MAKEFILE, 'to make', version.pkgfile, 'for libsodium', version.libsodium_version)
241	  return 0
242	
243	if __name__ == '__main__':
244	  sys.exit(main(sys.argv))
```

**`freebsd/contrib/libsodium/src/libsodium/crypto_onetimeauth/poly1305/onetimeauth_poly1305.c`** — implementation(constant)

```c
1	
2	#include "onetimeauth_poly1305.h"
3	#include "crypto_onetimeauth_poly1305.h"
4	#include "private/common.h"
5	#include "private/implementations.h"
6	#include "randombytes.h"
7	#include "runtime.h"
8	
9	#include "donna/poly1305_donna.h"
10	#if defined(HAVE_TI_MODE) && defined(HAVE_EMMINTRIN_H)
11	# include "sse2/poly1305_sse2.h"
12	#endif
13	
14	static const crypto_onetimeauth_poly1305_implementation *implementation =
15	    &crypto_onetimeauth_poly1305_donna_implementation;
16	
17	int
18	crypto_onetimeauth_poly1305(unsigned char *out, const unsigned char *in,
19	                            unsigned long long inlen, const unsigned char *k)
20	{
21	    return implementation->onetimeauth(out, in, inlen, k);
22	}
23	
24	int
25	crypto_onetimeauth_poly1305_verify(const unsigned char *h,
26	                                   const unsigned char *in,
27	                                   unsigned long long   inlen,
28	                                   const unsigned char *k)
29	{
30	    return implementation->onetimeauth_verify(h, in, inlen, k);
31	}
32	
33	int
34	crypto_onetimeauth_poly1305_init(crypto_onetimeauth_poly1305_state *state,
35	                                 const unsigned char *key)
36	{
37	    return implementation->onetimeauth_init(state, key);
38	}
39	
40	int
41	crypto_onetimeauth_poly1305_update(crypto_onetimeauth_poly1305_state *state,
42	                                   const unsigned char *in,
43	                                   unsigned long long inlen)
44	{
45	    return implementation->onetimeauth_update(state, in, inlen);
46	}
47	
48	int
49	crypto_onetimeauth_poly1305_final(crypto_onetimeauth_poly1305_state *state,
50	                                  unsigned char *out)
51	{
52	    return implementation->onetimeauth_final(state, out);
53	}
54	
55	size_t
56	crypto_onetimeauth_poly1305_bytes(void)
57	{
58	    return crypto_onetimeauth_poly1305_BYTES;
59	}
60	
61	size_t
62	crypto_onetimeauth_poly1305_keybytes(void)
63	{
64	    return crypto_onetimeauth_poly1305_KEYBYTES;
65	}
66	
67	size_t
68	crypto_onetimeauth_poly1305_statebytes(void)
69	{
70	    return sizeof(crypto_onetimeauth_poly1305_state);
71	}
72	
73	void
74	crypto_onetimeauth_poly1305_keygen(
75	    unsigned char k[crypto_onetimeauth_poly1305_KEYBYTES])
76	{
77	    randombytes_buf(k, crypto_onetimeauth_poly1305_KEYBYTES);
78	}
79	
80	int
81	_crypto_onetimeauth_poly1305_pick_best_implementation(void)
82	{
83	    implementation = &crypto_onetimeauth_poly1305_donna_implementation;
84	#if defined(HAVE_TI_MODE) && defined(HAVE_EMMINTRIN_H)
85	    if (sodium_runtime_has_sse2()) {
86	        implementation = &crypto_onetimeauth_poly1305_sse2_implementation;
87	    }
88	#endif
89	    return 0;
90	}
```


... (output truncated to budget; the source above is complete and verbatim — treat it as already Read. For any area not covered, run another codegraph_explore with the specific names — do NOT Read these files.)

## finding-871a4c5273dd — 配置代理地址时未发送非请求式 Neighbor Advertisement

Query: `Trace the implementation and all relevant callers for 配置代理地址时未发送非请求式 Neighbor Advertisement. Start from freebsd/netinet6/nd6_nbr.c symbol nd6_ns_input. Look specifically for an alternative implementation or counterevidence that would make the suspected design-to-code difference invalid.`

**Dynamic-dispatch links among your symbols**
(synthesized — the indirect hops grep/Read would reconstruct; the `@file:line` is the wiring site)

- ng_generic_msg → ngs_rcvmsg   [dynamic: fn-pointer ng_type.rcvmsg @freebsd/netgraph/ng_base.c:2934]

> Full source for these symbols is below — the call flow among them, followed by their bodies.
**Exploration: Trace the implementation and all relevant callers for 配置代理地址时未发送非请求式 Neighbor Advertisement. Start from freebsd/netinet6/nd6_nbr.c symbol nd6_ns_input. Look specifically for an alternative implementation or counterevidence that would make the suspected design-to-code difference invalid.**

Found 26 symbols across 4 files.

**Blast radius — what depends on these (update/verify before editing)**

- `nd6_ns_input` (freebsd/netinet6/nd6_nbr.c:126) — 2 callers in `freebsd/netinet6/icmp6.c`, `freebsd/netinet6/send.c`; ⚠️ no covering tests found
- `make` (freebsd/contrib/libsodium/packaging/dotnet-core/prepare.py:67) — 1 caller in `freebsd/contrib/libsodium/packaging/dotnet-core/prepare.py`; ⚠️ no covering tests found

**Relationships**

**calls:**
- nd6_ns_input → ip6_sprintf
- nd6_ns_input → if_name
- nd6_ns_input → m_pullup
- nd6_ns_input → in6_setscope
- nd6_ns_input → nd6_is_addr_neighbor
- nd6_ns_input → nd6_option_init
- nd6_ns_input → nd6_options
- nd6_ns_input → in6ifa_ifpwithaddr
- nd6_ns_input → nd6_proxy_fill_sdl
- nd6_ns_input → nd6_dad_ns_input
- nd6_ns_input → nd6_na_output_fib
- nd6_ns_input → nd6_cache_lladdr
- nd6_ns_input → ifa_free
- nd6_ns_input → m_freem
- icmp6_input → nd6_ns_input
- ... and 33 more

**instantiates:**
- main → WindowsItem
- main → Version
- main → MacOSItem
- main → LinuxItem
- main → ExtraItem

**references:**
- main → MAKEFILE
- main → DOCKER
- main → PROPSFILE
- main → EXTRAS
- main → LINUX
- main → MACOS
- main → WINDOWS
- __init__ → LIBRARY
- __init__ → CACHEDIR
- __init__ → LIBRARY
- __init__ → CACHEDIR
- make → DOCKER
- __init__ → LIBRARY
- __init__ → CACHEDIR
- __init__ → CACHEDIR

**Source Code**

> The code below is the **verbatim, current on-disk source** of these files — re-read from disk on this call and line-numbered, byte-for-byte identical to what the Read tool returns. It is NOT a summary, outline, or stale cache. Treat each block as a Read you have already performed: do not Read a file shown here.

**`freebsd/contrib/libsodium/src/libsodium/randombytes/randombytes.c`** — implementation(constant)

```c
1	
2	#include <assert.h>
3	#include <limits.h>
4	#include <stdint.h>
5	#include <stdlib.h>
6	
7	#include <sys/types.h>
8	
9	#ifdef __EMSCRIPTEN__
10	# include <emscripten.h>
11	#endif
12	
13	#include "core.h"
14	#include "crypto_stream_chacha20.h"
15	#include "randombytes.h"
16	#ifdef RANDOMBYTES_DEFAULT_IMPLEMENTATION
17	# include "randombytes_default.h"
18	#else
19	# ifdef __native_client__
20	#  include "randombytes_nativeclient.h"
21	# else
22	#  include "randombytes_sysrandom.h"
23	# endif
24	#endif
25	#include "private/common.h"
26	
27	/* C++Builder defines a "random" macro */
28	#undef random
29	
30	static const randombytes_implementation *implementation;
31	
32	#ifndef RANDOMBYTES_DEFAULT_IMPLEMENTATION
33	# ifdef __EMSCRIPTEN__
34	#  define RANDOMBYTES_DEFAULT_IMPLEMENTATION NULL
35	# else
36	#  ifdef __native_client__
37	#   define RANDOMBYTES_DEFAULT_IMPLEMENTATION &randombytes_nativeclient_implementation;
38	#  else
39	#   define RANDOMBYTES_DEFAULT_IMPLEMENTATION &randombytes_sysrandom_implementation;
40	#  endif
41	# endif
42	#endif
43	
44	static void
45	randombytes_init_if_needed(void)
46	{
47	    if (implementation == NULL) {
48	        implementation = RANDOMBYTES_DEFAULT_IMPLEMENTATION;
49	        randombytes_stir();
50	    }
51	}
52	
53	int
54	randombytes_set_implementation(randombytes_implementation *impl)
55	{
56	    implementation = impl;
57	
58	    return 0;
59	}
60	
61	const char *
62	randombytes_implementation_name(void)
63	{
64	#ifndef __EMSCRIPTEN__
65	    randombytes_init_if_needed();
66	    return implementation->implementation_name();
67	#else
68	    return "js";
69	#endif
70	}
71	
72	uint32_t
73	randombytes_random(void)
74	{
75	#ifndef __EMSCRIPTEN__
76	    randombytes_init_if_needed();
77	    return implementation->random();
78	#else
79	    return EM_ASM_INT_V({
80	        return Module.getRandomValue();
81	    });
82	#endif
83	}
84	
85	void
86	randombytes_stir(void)
87	{
88	#ifndef __EMSCRIPTEN__
89	    randombytes_init_if_needed();
90	    if (implementation->stir != NULL) {
91	        implementation->stir();
92	    }
93	#else
94	    EM_ASM({
95	        if (Module.getRandomValue === undefined) {
96	            try {
97	                var window_ = 'object' === typeof window ? window : self;
98	                var crypto_ = typeof window_.crypto !== 'undefined' ? window_.crypto : window_.msCrypto;
99	                var randomValuesStandard = function() {
100	                    var buf = new Uint32Array(1);
101	                    crypto_.getRandomValues(buf);
102	                    return buf[0] >>> 0;
103	                };
104	                randomValuesStandard();
105	                Module.getRandomValue = randomValuesStandard;
106	            } catch (e) {
107	                try {
108	                    var crypto = require('crypto');
109	                    var randomValueNodeJS = function() {
110	                        var buf = crypto['randomBytes'](4);
111	                        return (buf[0] << 24 | buf[1] << 16 | buf[2] << 8 | buf[3]) >>> 0;
112	                    };
113	                    randomValueNodeJS();
114	                    Module.getRandomValue = randomValueNodeJS;
115	                } catch (e) {
116	                    throw 'No secure random number generator found';
117	                }
118	            }
119	        }
120	    });
121	#endif
122	}
123	
124	uint32_t
125	randombytes_uniform(const uint32_t upper_bound)
126	{
127	    uint32_t min;
128	    uint32_t r;
129	
130	#ifndef __EMSCRIPTEN__
131	    randombytes_init_if_needed();
132	    if (implementation->uniform != NULL) {
133	        return implementation->uniform(upper_bound);
134	    }
135	#endif
136	    if (upper_bound < 2) {
137	        return 0;
138	    }
139	    min = (1U + ~upper_bound) % upper_bound; /* = 2**32 mod upper_bound */
140	    do {
141	        r = randombytes_random();
142	    } while (r < min);
143	    /* r is now clamped to a set whose size mod upper_bound == 0
144	     * the worst case (2**31+1) requires ~ 2 attempts */
145	
146	    return r % upper_bound;
147	}
148	
149	void
150	randombytes_buf(void * const buf, const size_t size)
151	{
152	#ifndef __EMSCRIPTEN__
153	    randombytes_init_if_needed();
154	    if (size > (size_t) 0U) {
155	        implementation->buf(buf, size);
156	    }
157	#else
158	    unsigned char *p = (unsigned char *) buf;
159	    size_t         i;
160	
161	    for (i = (size_t) 0U; i < size; i++) {
162	        p[i] = (unsigned char) randombytes_random();
163	    }
164	#endif
165	}
166	
167	void
168	randombytes_buf_deterministic(void * const buf, const size_t size,
169	                              const unsigned char seed[randombytes_SEEDBYTES])
170	{
171	    static const unsigned char nonce[crypto_stream_chacha20_ietf_NONCEBYTES] = {
172	        'L', 'i', 'b', 's', 'o', 'd', 'i', 'u', 'm', 'D', 'R', 'G'
173	    };
174	
175	    COMPILER_ASSERT(randombytes_SEEDBYTES == crypto_stream_chacha20_ietf_KEYBYTES);
176	#if SIZE_MAX > 0x4000000000ULL
177	    COMPILER_ASSERT(randombytes_BYTES_MAX <= 0x4000000000ULL);
178	    if (size > 0x4000000000ULL) {
179	        sodium_misuse();
180	    }
181	#endif
182	    crypto_stream_chacha20_ietf((unsigned char *) buf, (unsigned long long) size,
183	                                nonce, seed);
184	}
185	
186	size_t
187	randombytes_seedbytes(void)
188	{
189	    return randombytes_SEEDBYTES;
190	}
191	
192	int
193	randombytes_close(void)
194	{
195	    if (implementation != NULL && implementation->close != NULL) {
196	        return implementation->close();
197	    }
198	    return 0;
199	}
200	
201	void
202	randombytes(unsigned char * const buf, const unsigned long long buf_len)
203	{
204	    assert(buf_len <= SIZE_MAX);
205	    randombytes_buf(buf, (size_t) buf_len);
206	}
```

**`freebsd/contrib/libsodium/packaging/dotnet-core/prepare.py`** — make(method), WindowsItem(class), main(function), __init__(method), Version(class), MacOSItem(class), LinuxItem(class), ExtraItem(class), MAKEFILE(variable), DOCKER(variable), PROPSFILE(variable), EXTRAS(variable), LINUX(variable), MACOS(variable), WINDOWS(variable), +2 more

```python
1	#!/usr/bin/env python3
2	
3	import os.path
4	import re
5	import sys
6	
7	WINDOWS = [
8	  # --------------------- ----------------- #
9	  # Runtime ID            Platform          #
10	  # --------------------- ----------------- #
11	  ( 'win-x64',            'x64'             ),
12	  ( 'win-x86',            'Win32'           ),
13	  # --------------------- ----------------- #
14	]
15	
16	MACOS = [
17	  # --------------------- ----------------- #
18	  # Runtime ID            Codename          #
19	  # --------------------- ----------------- #
20	  ( 'osx-x64',            'sierra'          ),
21	  # --------------------- ----------------- #
22	]
23	
24	LINUX = [
25	  # --------------------- ----------------- #
26	  # Runtime ID            Docker Image      #
27	  # --------------------- ----------------- #
28	  ( 'linux-x64',          'debian:stretch'  ),
29	  # --------------------- ----------------- #
30	]
31	
32	EXTRAS = [ 'LICENSE', 'AUTHORS', 'ChangeLog' ]
33	
34	PROPSFILE = 'libsodium.props'
35	MAKEFILE = 'Makefile'
36	BUILDDIR = 'build'
37	CACHEDIR = 'cache'
38	TEMPDIR = 'temp'
39	
40	PACKAGE = 'libsodium'
41	LIBRARY = 'libsodium'
42	
43	DOCKER = 'sudo docker'
44	
45	class Version:
46	
47	  def __init__(self, libsodium_version, package_version):
48	    self.libsodium_version = libsodium_version
49	    self.package_version = package_version
50	
51	    self.builddir = os.path.join(BUILDDIR, libsodium_version)
52	    self.tempdir = os.path.join(TEMPDIR, libsodium_version)
53	    self.projfile = os.path.join(self.builddir, '{0}.{1}.pkgproj'.format(PACKAGE, package_version))
54	    self.propsfile = os.path.join(self.builddir, '{0}.props'.format(PACKAGE))
55	    self.pkgfile = os.path.join(BUILDDIR, '{0}.{1}.nupkg'.format(PACKAGE, package_version))
56	
57	class WindowsItem:
58	
59	  def __init__(self, version, rid, platform):
60	    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}-msvc.zip'.format(version.libsodium_version)
61	    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
62	    self.packfile = os.path.join(version.builddir, 'runtimes', rid, 'native', LIBRARY + '.dll')
63	    self.itemfile = '{0}/Release/v140/dynamic/libsodium.dll'.format(platform)
64	    self.tempdir = os.path.join(version.tempdir, rid)
65	    self.tempfile = os.path.join(self.tempdir, os.path.normpath(self.itemfile))
66	
67	  def make(self, f):
68	    f.write('\n')
69	    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
70	    f.write('\t@mkdir -p $(dir $@)\n')
71	    f.write('\tcp -f $< $@\n')
72	    f.write('\n')
73	    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
74	    f.write('\t@mkdir -p $(dir $@)\n')
75	    f.write('\tcd {0} && unzip -q -DD -o {1} \'{2}\'\n'.format(
76	      self.tempdir,
77	      os.path.relpath(self.cachefile, self.tempdir),
78	      self.itemfile
79	    ))
80	
81	class MacOSItem:
82	
83	  def __init__(self, version, rid, codename):
84	    self.url = 'https://bintray.com/homebrew/bottles/download_file?file_path=libsodium-{0}.{1}.bottle.tar.gz'.format(version.libsodium_version, codename)
85	    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
86	    self.packfile = os.path.join(version.builddir, 'runtimes', rid, 'native', LIBRARY + '.dylib')
87	    self.itemfile = 'libsodium/{0}/lib/libsodium.dylib'.format(version.libsodium_version)
88	    self.tempdir = os.path.join(version.tempdir, rid)
89	    self.tempfile = os.path.join(self.tempdir, os.path.normpath(self.itemfile))
90	
91	  def make(self, f):
92	    f.write('\n')
93	    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
94	    f.write('\t@mkdir -p $(dir $@)\n')
95	    f.write('\tcp -f $< $@\n')
96	    f.write('\n')
97	    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
98	    f.write('\t@mkdir -p $(dir $@)\n')
99	    f.write('\tcd {0} && tar xzmf {1} \'{2}\'\n'.format(
100	      self.tempdir,
101	      os.path.relpath(self.cachefile, self.tempdir),
102	      os.path.dirname(self.itemfile)
103	    ))
104	
105	class LinuxItem:
106	
107	  def __init__(self, version, rid, docker_image):
108	    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}.tar.gz'.format(version.libsodium_version)
109	    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
110	    self.packfile = os.path.join(version.builddir, 'runtimes', rid, 'native', LIBRARY + '.so')
111	    self.tempdir = os.path.join(version.tempdir, rid)
112	    self.tempfile = os.path.join(self.tempdir, 'libsodium.so')
113	    self.docker_image = docker_image
114	    self.recipe = rid
115	
116	  def make(self, f):
117	    recipe = self.recipe
118	    while not os.path.exists(os.path.join('recipes', recipe)):
119	      m = re.fullmatch(r'([^.-]+)((([.][^.-]+)*)[.][^.-]+)?([-].*)?', recipe)
120	      if m.group(5) is None:
121	        recipe = 'build'
122	        break
123	      elif m.group(2) is None:
124	        recipe = m.group(1)
125	      else:
126	        recipe = m.group(1) + m.group(3) + m.group(5)
127	
128	    f.write('\n')
129	    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
130	    f.write('\t@mkdir -p $(dir $@)\n')
131	    f.write('\tcp -f $< $@\n')
132	    f.write('\n')
133	    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
134	    f.write('\t@mkdir -p $(dir $@)\n')
135	    f.write('\t{0} run --rm '.format(DOCKER) +
136	            '-v $(abspath recipes):/io/recipes ' +
137	            '-v $(abspath $<):/io/libsodium.tar.gz ' +
138	            '-v $(abspath $(dir $@)):/io/output ' +
139	            '{0} sh -x -e /io/recipes/{1}\n'.format(self.docker_image, recipe))
140	
141	class ExtraItem:
142	
143	  def __init__(self, version, filename):
144	    self.url = 'https://download.libsodium.org/libsodium/releases/libsodium-{0}.tar.gz'.format(version.libsodium_version)
145	    self.cachefile = os.path.join(CACHEDIR, re.sub(r'[^A-Za-z0-9.]', '-', self.url))
146	    self.packfile = os.path.join(version.builddir, filename)
147	    self.itemfile = 'libsodium-{0}/{1}'.format(version.libsodium_version, filename)
148	    self.tempdir = os.path.join(version.tempdir, 'extras')
149	    self.tempfile = os.path.join(self.tempdir, os.path.normpath(self.itemfile))
150	
151	  def make(self, f):
152	    f.write('\n')
153	    f.write('{0}: {1}\n'.format(self.packfile, self.tempfile))
154	    f.write('\t@mkdir -p $(dir $@)\n')
155	    f.write('\tcp -f $< $@\n')
156	    f.write('\n')
157	    f.write('{0}: {1}\n'.format(self.tempfile, self.cachefile))
158	    f.write('\t@mkdir -p $(dir $@)\n')
159	    f.write('\tcd {0} && tar xzmf {1} \'{2}\'\n'.format(
160	      self.tempdir,
161	      os.path.relpath(self.cachefile, self.tempdir),
162	      self.itemfile
163	    ))
164	
165	def main(args):
166	  m = re.fullmatch(r'((\d+\.\d+\.\d+)(\.\d+)?)(?:-(\w+(?:[_.-]\w+)*))?', args[1]) if len(args) == 2 else None
167	
168	  if m is None:
169	    print('Usage:')
170	    print('       python3 prepare.py <version>')
171	    print()
172	    print('Examples:')
173	    print('       python3 prepare.py 1.0.16-preview-01')
174	    print('       python3 prepare.py 1.0.16-preview-02')
175	    print('       python3 prepare.py 1.0.16-preview-03')
176	    print('       python3 prepare.py 1.0.16')
177	    print('       python3 prepare.py 1.0.16.1-preview-01')
178	    print('       python3 prepare.py 1.0.16.1')
179	    print('       python3 prepare.py 1.0.16.2')
180	    return 1
181	
182	  version = Version(m.group(2), m.group(0))
183	
184	  items = [ WindowsItem(version, rid, platform)   for (rid, platform) in WINDOWS   ] + \
185	          [ MacOSItem(version, rid, codename)     for (rid, codename) in MACOS     ] + \
186	          [ LinuxItem(version, rid, docker_image) for (rid, docker_image) in LINUX ] + \
187	          [ ExtraItem(version, filename)          for filename in EXTRAS           ]
188	
189	  downloads = {item.cachefile: item.url for item in items}
190	
191	  with open(MAKEFILE, 'w') as f:
192	    f.write('all: {0}\n'.format(version.pkgfile))
193	
194	    for download in sorted(downloads):
195	      f.write('\n')
196	      f.write('{0}:\n'.format(download))
197	      f.write('\t@mkdir -p $(dir $@)\n')
198	      f.write('\tcurl -f#Lo $@ \'{0}\'\n'.format(downloads[download]))
199	
200	    for item in items:
201	      item.make(f)
202	
203	    f.write('\n')
204	    f.write('{0}: {1}\n'.format(version.propsfile, PROPSFILE))
205	    f.write('\t@mkdir -p $(dir $@)\n')
206	    f.write('\tcp -f $< $@\n')
207	
208	    f.write('\n')
209	    f.write('{0}: {1}\n'.format(version.projfile, version.propsfile))
210	    f.write('\t@mkdir -p $(dir $@)\n')
211	    f.write('\techo \'' +
212	            '<Project Sdk="Microsoft.NET.Sdk">' +
213	            '<Import Project="{0}" />'.format(os.path.relpath(version.propsfile, os.path.dirname(version.projfile))) +
214	            '<PropertyGroup>' +
215	            '<Version>{0}</Version>'.format(version.package_version) +
216	            '</PropertyGroup>' +
217	            '</Project>\' > $@\n')
218	
219	    f.write('\n')
220	    f.write('{0}:'.format(version.pkgfile))
221	    f.write(' \\\n\t\t{0}'.format(version.projfile))
222	    f.write(' \\\n\t\t{0}'.format(version.propsfile))
223	    for item in items:
224	      f.write(' \\\n\t\t{0}'.format(item.packfile))
225	    f.write('\n')
226	    f.write('\t@mkdir -p $(dir $@)\n')
227	    f.write('\t{0} run --rm '.format(DOCKER) +
228	            '-v $(abspath recipes):/io/recipes ' +
229	            '-v $(abspath $(dir $<)):/io/input ' +
230	            '-v $(abspath $(dir $@)):/io/output ' +
231	            '{0} sh -x -e /io/recipes/{1} {2}\n'.format('microsoft/dotnet:2.0-sdk', 'pack', os.path.relpath(version.projfile, version.builddir)))
232	
233	    f.write('\n')
234	    f.write('test: {0}\n'.format(version.pkgfile))
235	    f.write('\t{0} run --rm '.format(DOCKER) +
236	            '-v $(abspath recipes):/io/recipes ' +
237	            '-v $(abspath $(dir $<)):/io/packages ' +
238	            '{0} sh -x -e /io/recipes/{1} "{2}"\n'.format('microsoft/dotnet:2.0-sdk', 'test', version.package_version))
239	
240	  print('prepared', MAKEFILE, 'to make', version.pkgfile, 'for libsodium', version.libsodium_version)
241	  return 0
242	
243	if __name__ == '__main__':
244	  sys.exit(main(sys.argv))
```

**`freebsd/contrib/libsodium/src/libsodium/crypto_onetimeauth/poly1305/onetimeauth_poly1305.c`** — implementation(constant)

```c
1	
2	#include "onetimeauth_poly1305.h"
3	#include "crypto_onetimeauth_poly1305.h"
4	#include "private/common.h"
5	#include "private/implementations.h"
6	#include "randombytes.h"
7	#include "runtime.h"
8	
9	#include "donna/poly1305_donna.h"
10	#if defined(HAVE_TI_MODE) && defined(HAVE_EMMINTRIN_H)
11	# include "sse2/poly1305_sse2.h"
12	#endif
13	
14	static const crypto_onetimeauth_poly1305_implementation *implementation =
15	    &crypto_onetimeauth_poly1305_donna_implementation;
16	
17	int
18	crypto_onetimeauth_poly1305(unsigned char *out, const unsigned char *in,
19	                            unsigned long long inlen, const unsigned char *k)
20	{
21	    return implementation->onetimeauth(out, in, inlen, k);
22	}
23	
24	int
25	crypto_onetimeauth_poly1305_verify(const unsigned char *h,
26	                                   const unsigned char *in,
27	                                   unsigned long long   inlen,
28	                                   const unsigned char *k)
29	{
30	    return implementation->onetimeauth_verify(h, in, inlen, k);
31	}
32	
33	int
34	crypto_onetimeauth_poly1305_init(crypto_onetimeauth_poly1305_state *state,
35	                                 const unsigned char *key)
36	{
37	    return implementation->onetimeauth_init(state, key);
38	}
39	
40	int
41	crypto_onetimeauth_poly1305_update(crypto_onetimeauth_poly1305_state *state,
42	                                   const unsigned char *in,
43	                                   unsigned long long inlen)
44	{
45	    return implementation->onetimeauth_update(state, in, inlen);
46	}
47	
48	int
49	crypto_onetimeauth_poly1305_final(crypto_onetimeauth_poly1305_state *state,
50	                                  unsigned char *out)
51	{
52	    return implementation->onetimeauth_final(state, out);
53	}
54	
55	size_t
56	crypto_onetimeauth_poly1305_bytes(void)
57	{
58	    return crypto_onetimeauth_poly1305_BYTES;
59	}
60	
61	size_t
62	crypto_onetimeauth_poly1305_keybytes(void)
63	{
64	    return crypto_onetimeauth_poly1305_KEYBYTES;
65	}
66	
67	size_t
68	crypto_onetimeauth_poly1305_statebytes(void)
69	{
70	    return sizeof(crypto_onetimeauth_poly1305_state);
71	}
72	
73	void
74	crypto_onetimeauth_poly1305_keygen(
75	    unsigned char k[crypto_onetimeauth_poly1305_KEYBYTES])
76	{
77	    randombytes_buf(k, crypto_onetimeauth_poly1305_KEYBYTES);
78	}
79	
80	int
81	_crypto_onetimeauth_poly1305_pick_best_implementation(void)
82	{
83	    implementation = &crypto_onetimeauth_poly1305_donna_implementation;
84	#if defined(HAVE_TI_MODE) && defined(HAVE_EMMINTRIN_H)
85	    if (sodium_runtime_has_sse2()) {
86	        implementation = &crypto_onetimeauth_poly1305_sse2_implementation;
87	    }
88	#endif
89	    return 0;
90	}
```

**`freebsd/contrib/libsodium/src/libsodium/crypto_scalarmult/curve25519/scalarmult_curve25519.c`** — implementation(constant)

```c
1	
2	#include "crypto_scalarmult_curve25519.h"
3	#include "private/implementations.h"
4	#include "scalarmult_curve25519.h"
5	#include "runtime.h"
6	
7	#ifdef HAVE_AVX_ASM
8	# include "sandy2x/curve25519_sandy2x.h"
9	#endif
10	#include "ref10/x25519_ref10.h"
11	static const crypto_scalarmult_curve25519_implementation *implementation =
12	    &crypto_scalarmult_curve25519_ref10_implementation;
13	
14	int
15	crypto_scalarmult_curve25519(unsigned char *q, const unsigned char *n,
16	                             const unsigned char *p)
17	{
18	    size_t                 i;
19	    volatile unsigned char d = 0;
20	
21	    if (implementation->mult(q, n, p) != 0) {
22	        return -1; /* LCOV_EXCL_LINE */
23	    }
24	    for (i = 0; i < crypto_scalarmult_curve25519_BYTES; i++) {
25	        d |= q[i];
26	    }
27	    return -(1 & ((d - 1) >> 8));
28	}
29	
30	int
31	crypto_scalarmult_curve25519_base(unsigned char *q, const unsigned char *n)
32	{
33	    return implementation->mult_base(q, n);
34	}
35	
36	size_t
37	crypto_scalarmult_curve25519_bytes(void)
38	{
39	    return crypto_scalarmult_curve25519_BYTES;
40	}
41	
42	size_t
43	crypto_scalarmult_curve25519_scalarbytes(void)
44	{
45	    return crypto_scalarmult_curve25519_SCALARBYTES;
46	}
47	
48	int
49	_crypto_scalarmult_curve25519_pick_best_implementation(void)
50	{
51	    implementation = &crypto_scalarmult_curve25519_ref10_implementation;
52	
53	#ifdef HAVE_AVX_ASM
54	    if (sodium_runtime_has_avx()) {
55	        implementation = &crypto_scalarmult_curve25519_sandy2x_implementation;
56	    }
57	#endif
58	    return 0;
59	}
```


... (output truncated to budget; the source above is complete and verbatim — treat it as already Read. For any area not covered, run another codegraph_explore with the specific names — do NOT Read these files.)
