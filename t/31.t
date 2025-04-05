#!/usr/bin/perl

# timmy insta reel urls in last 2 weeks...currently 03-05-25

use strict;
use warnings;
use Test::More;
use File::Spec;
use FindBin;
use Cwd 'abs_path';
use Log::Log4perl;
use File::Path 'make_path';
use Acme::Frobnitz;

# Set up logging
my $log_dir = File::Spec->catdir($FindBin::Bin, '..', 'logs');
my $log_file = File::Spec->catfile($log_dir, 'acme-frobnitz.log');

unless (-d $log_dir) {
    eval { make_path($log_dir) };
    die "Failed to create log directory $log_dir: $@" if $@;
}

my $log_config = qq(
log4perl.logger = INFO, FileAppender
log4perl.appender.FileAppender = Log::Log4perl::Appender::File
log4perl.appender.FileAppender.filename = $log_file
log4perl.appender.FileAppender.layout = Log::Log4perl::Layout::PatternLayout
log4perl.appender.FileAppender.layout.ConversionPattern = %d [%p] %m%n
);
Log::Log4perl->init(\$log_config);
my $logger = Log::Log4perl->get_logger();

# Instantiate Frobnitz object
my $frobnitz = Acme::Frobnitz->new();


# Mar 12 to

# Define list of URLs (from your clips/1.timmy.txt)
my @video_urls = (
    '

	'https://www.youtube.com/watch?v=7Yhnml4DW9g',
);

# Process each video URL
foreach my $video_url (@video_urls) {
    $logger->info("Starting download for URL: $video_url");
    my $download_output = $frobnitz->call_dispatch($video_url);
    my ($last_line) = (split /\n/, $download_output)[-1];
    chomp($last_line);




}

done_testing();

