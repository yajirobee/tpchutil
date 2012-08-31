CREATE UNIQUE INDEX n_nationkey_idx on nation (n_nationkey);
CREATE UNIQUE INDEX r_regionkey_idx on region (r_regionkey);
CREATE UNIQUE INDEX p_partkey_idx on part (p_partkey);
CREATE UNIQUE INDEX s_suppkey_idx on supplier (s_suppkey);
CREATE UNIQUE INDEX ps_partsuppkey_idx on partsupp (ps_partkey, ps_suppkey);
CREATE UNIQUE INDEX c_custkey_idx on customer (c_custkey);
CREATE UNIQUE INDEX o_orderkey_idx on orders (o_orderkey);
CREATE UNIQUE INDEX l_orderlinekey_idx on lineitem (l_orderkey, l_linenumber);
