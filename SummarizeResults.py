import os, sys, csv, glob, re

__author__ = 'dankerrigan'

from operator import itemgetter, attrgetter

class Summary:
    def __init__(self):
        self.reset()

    def add(self, value):
        if value not in self.values:
            self.values[value] = 1
        else:
            self.values[value] += 1
        self.count += 1

    def add_many(self, values):
        for value in values:
            self.add(value)

    def add_dict(self, dict_values):
        self.values = dict_values.copy()
        self.count = sum(dict_values.values())

    def add_summary(self, summary):
        for key in summary.values:
            bucket = self.values.get(key, 0)
            bucket += summary.values[key]
            self.values[key] = bucket
            self.count += summary.values[key]

    def reset(self):
        self.values = {}
        self.count = 0

    def spread(self):
        return min(self.values.keys()), max(self.values.keys())

    def sum_values(self):
        return sum([value * count for  value, count in self.values.items()])

    def min(self):
        return min(self.values.keys())

    def max(self):
        return max(self.values.keys())

    def mean(self):
        numerator = self.sum_values()
        return float(numerator)/float(self.count)

    def median(self):
        center = len(self.values.items())/2
        return sorted([value * count for  value, count in self.values.items()])[center]

    def variance(self):
        mu = self.mean()
        s = 0
        for value, count in self.values.items():
            s += ((value-mu)**2)*count
        return float(s)/(self.count-1)

    def stdev(self):
        return self.variance()**.5

    def modes(self):
        return sorted(self.values.items(), key=itemgetter(1), reverse=True)

    def histogram(self):
        return self.values

    def pmf(self):
        pmf = {}
        for value in self.values:
            pmf[value] = float(self.values[value]) / float(self.count)
        return pmf

    def hist_range(self, start, stop, hist=None):
        if not hist:
            hist = self.values.copy()
        else:
            hist = hist.copy()
        keys = range(start, stop + 1)
        for key in keys:
            if key not in hist:
                hist[key] = 0
        return hist

    def pmf_range(self, start, stop):
        return self.hist_range(start, stop, hist=self.pmf())

    def cdf(self, hist=None):
        cdf_hist = {}
        total = 0
        if not hist:
            hist = self.values

        for key in sorted(hist.keys()):
            total += hist[key] * key
            cdf_hist[key] = total
        return cdf_hist

    def cdf_range(self, start, stop):
        hist = self.hist_range(start, stop)
        return self.cdf(hist)

class ResultsSummarizer(object):
    _results_path = None
    _latency_summary_fields = ['filename','elapsed','n','min','mean','median','95','99','99.9','max','errors','ops/sec']

    def __init__(self, results_path):
        self._results_path = results_path

    def _create_latency_summary_dict(self):

        summary_dict = {}
        for field in self._latency_summary_fields:
            summary_dict[field] = Summary()
        return summary_dict

    def summarize_basho_bench_latency(self, filename):
        count = 0

        summary_dict = self._create_latency_summary_dict()
        with open(filename, 'rb') as summary_file:
            reader = csv.reader(summary_file)
            reader.next()

            for row in reader:
                row = map(str.strip, row)
                vals = map(float, row)
                elapsed, window, n, min, mean, median, nine5, nine9, nine9_9, max, errors = vals[:11]
                summary_dict['filename'] = filename
                summary_dict['elapsed'].add(elapsed)
                summary_dict['n'].add(n)
                summary_dict['min'].add(min/1000)
                summary_dict['mean'].add(mean/1000)
                summary_dict['median'].add(median/1000)
                summary_dict['95'].add(nine5/1000)
                summary_dict['99'].add(nine9/1000)
                summary_dict['99.9'].add(nine9_9/1000)
                summary_dict['max'].add(max/1000)
                summary_dict['errors'].add(errors)
                summary_dict['ops/sec'].add(n/window)

        return summary_dict


    def summarize_basho_bench_summary(self, filename):
        count = 0
        min = 999999
        max = -1
        avg_agg = 0
        with open(filename, 'rb') as summary_file:
            reader = csv.reader(summary_file)
            reader.next()

            for row in reader:
                row = map(str.strip, row)
                vals = map(float, row)
                elapsed, window, total, successful, failed = vals[:5]
                avg = total/window
                avg_agg += avg
                count += 1

        return avg_agg/count
    
    def simplify_filename(self, filename):
        matchObj = re.match( r'results\/baseline_(.*)-(.*)-(.*)\/(.*)\/(.*)\/(.*)_latencies.csv', filename, re.M|re.I)
        
        if matchObj:
            protocol = matchObj.group(1)
            version = matchObj.group(2)
            backend = matchObj.group(3)
            
            if (matchObj.group(4) == "tag_RiakServers_cluster1"):
                cluster = "AWS"
            else:
                cluster = "SL"
            timestamp = matchObj.group(5)
            operation = matchObj.group(6)
            return "[" + cluster + "] " + protocol + "." + backend + "." + operation + " (" + version + ") TS:" + timestamp
        else:
            return filename

    def summarize_basho_bench_results(self, path):
        latency_wc = '*latencies.csv'
        full_path = path + os.path.sep + latency_wc
        files = glob.glob(full_path)

        for latency_file in files:
            latency_stat = self.summarize_basho_bench_latency(latency_file)
            if len(latency_stat) != 0:
                latency_stat['name'] = self.simplify_filename(latency_file)
                latency_stat['filename'] = latency_file
                yield latency_stat
    
    def find_dirs(self, path):
        dirs = os.listdir(path)
        dirs = [path + os.path.sep + dir for dir in dirs]
        dirs = [dir for dir in dirs if os.path.isdir(dir)]
        return dirs

    def summarize_result_dirs(self):
        test_dirs = self.find_dirs(self._results_path)
        all_stats = []
        
        for dir in test_dirs:
            cluster_dirs = self.find_dirs(dir)
            for dir in cluster_dirs:
                iteration_dirs = self.find_dirs(dir)
                for dir in iteration_dirs:
                    stats = self.summarize_basho_bench_results(dir)
                    map(all_stats.append, stats)

        return all_stats

    def aggregate_similar_folders(self, stats):
        aggregated_stats = {}
        for stat in stats:
            name = stat['name']

            aggregated_stats[name] = stat
            #path, filename = os.path.split(filename)
            ind = name.rfind('TS:')
            group_path = name[:ind]
            agg_stat = aggregated_stats.get(group_path, self._create_latency_summary_dict())
            agg_stat = self._add_summary_dicts(agg_stat, stat)
            agg_stat['filename'] = "rollup"
            aggregated_stats["rollup " + group_path] = agg_stat

        return aggregated_stats

#        aggregated_stats = {}
#        for stat in stats:
#            filename = stat['filename']
#
#            aggregated_stats[filename] = stat
#            path, filename = os.path.split(filename)
#            ind = path.rfind('2013')
#            group_path = path[:ind]
#            agg_stat = aggregated_stats.get(group_path, self._create_latency_summary_dict())
#            agg_stat = self._add_summary_dicts(agg_stat, stat)
#            aggregated_stats[group_path] = agg_stat
#
#        return aggregated_stats

    def calculate_results(self, summary_stats):
        for name, summary_stat in summary_stats.items():
            stat = {}
            stat['name'] = name
            stat['filename'] = summary_stat['filename']
            stat['elapsed'] = summary_stat['elapsed'].max()
            stat['n'] = summary_stat['n'].sum_values()
            stat['min'] = summary_stat['min'].min()
            stat['mean'] = summary_stat['mean'].mean()
            stat['mean_std_dev'] = summary_stat['mean'].stdev()
            stat['median'] = summary_stat['median'].median()
            stat['95'] = summary_stat['95'].median()
            stat['99'] = summary_stat['99'].median()
            stat['99.9'] = summary_stat['99.9'].median()
            stat['max'] = summary_stat['max'].max()
            stat['errors'] = summary_stat['errors'].sum_values()
            stat['mean_ops/sec'] = summary_stat['ops/sec'].mean()
            stat['mean_ops/sec_std_dev'] = summary_stat['ops/sec'].stdev()
            yield stat


    def _add_summary_dicts(self, dict1, dict2):
        for field in self._latency_summary_fields:
            if field != "filename":
                dict1[field].add_summary(dict2[field]) 
        return dict1

if __name__ == '__main__':
    base_path = sys.argv[1]

    summarizer = ResultsSummarizer(base_path)
    aggregated_stats = summarizer.aggregate_similar_folders(summarizer.summarize_result_dirs())
    #calculated_stats = summarizer.calculate_results(aggregated_stats)
    #summarizer.print_stats(calculated_stats)
    
    key_order = ['name',
                 'elapsed',
                 'n',
                 'min',
                 'mean',
                 'mean_std_dev',
                 'median',
                 '95',
                 '99',
                 '99.9',
                 'max',
                 'errors',
                 'mean_ops/sec',
                 'mean_ops/sec_std_dev']

    print ','.join(key_order)
    
    for stat in sorted(summarizer.calculate_results(aggregated_stats),key=itemgetter('name')):
        print ','.join([str(stat[key]) for key in key_order])

    print " "
    print " "
    print " "
    
    summary_results = {}
    for stat in sorted(summarizer.calculate_results(aggregated_stats),key=itemgetter('name')):
        name = stat['name']
        ind = name.rfind('rollup')
        if (ind >= 0):
            ind121 = name.rfind(' (1.2.1')
            ind13 = name.rfind(' (1.3')
            if (ind121 >= 0):
                summary_results[name[:ind121]] = []
                summary_results[name[:ind121]].append(stat['mean'])
            elif (ind13 >= 0):
                summary_results[name[:ind13]].append(stat['mean'])
                
    print "Name,1.2.1 Mean Latency,1.3 Mean Latency"
    
    for name, result in sorted(summary_results.items()):
        line = re.sub('rollup ', '', name) + "," + str(result[0]) + ","
        if 1 < len(result):
            line += str(result[1])
        print line