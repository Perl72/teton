#!/usr/bin/perl

use strict;
use warnings;
use Test::More;
use File::Spec;
use FindBin;
use Cwd 'abs_path';
use Log::Log4perl;
use File::Path 'make_path';
use Carp 'longmess';

# Set up logging
my $log_dir  = File::Spec->catdir($FindBin::Bin, '..', 'logs');
my $log_file = File::Spec->catfile($log_dir, 'acme-frobnitz.log');

unless (-d $log_dir) {
    eval { make_path($log_dir) };
    die "Failed to create log directory $log_dir: $@" if $@;
}

my $log_config = qq(
log4perl.logger                         = INFO, Logfile
log4perl.appender.Logfile               = Log::Log4perl::Appender::File
log4perl.appender.Logfile.filename      = $log_file
log4perl.appender.Logfile.layout        = Log::Log4perl::Layout::PatternLayout
log4perl.appender.Logfile.layout.ConversionPattern = [%d] [%p] %m%n
);

Log::Log4perl->init(\$log_config);
my $logger = Log::Log4perl->get_logger();

# Load Frobnitz
use lib "$FindBin::Bin/../lib";
use Acme::Frobnitz;

my $frobnitz = Acme::Frobnitz->new();

# Read test URL from @ARGV or fallback
my $test_url = $ARGV[0] // 'https://www.instagram.com/p/DI1mHmsxllI/';
$logger->info("▶️ Starting test for: $test_url");

# Test download method exists
can_ok('Acme::Frobnitz', 'download') or do {
    $logger->fatal("❌ 'download' method not found");
    BAIL_OUT("download method missing");
};

# Step 1: Attempt download
my $output_file;
eval {
    $output_file = $frobnitz->download($test_url);
};
if ($@) {
    my $bt = longmess($@);
    $logger->error("❌ Download failed: $@");
    $logger->error("📍 Backtrace:\n$bt");
    fail("Download threw an exception");
    BAIL_OUT("Aborting test after failed download.");
}

ok($output_file, "✅ Download completed");
$logger->info("Download output: $output_file");

# Step 2: Verify file
my ($downloaded_file) = (split /\n/, $output_file)[-1];
chomp($downloaded_file);

if ($frobnitz->verify_file($downloaded_file)) {
    pass("✅ File verification passed");
    $logger->info("Verified downloaded file: $downloaded_file");
} else {
    fail("❌ File verification failed");
    $logger->fatal("Verification failed for: $downloaded_file");
    BAIL_OUT("Aborting test after failed verification.");
}

# Step 3: Watermark
my $watermarked_file;
eval {
    $watermarked_file = $frobnitz->add_watermark($downloaded_file);
};
if ($@) {
    my $bt = longmess($@);
    $logger->error("❌ Watermarking failed: $@");
    $logger->error("📍 Backtrace:\n$bt");
    fail("Watermarking threw an exception");
    BAIL_OUT("Aborting test after failed watermarking.");
}

ok($watermarked_file, "✅ Watermarking completed");
$logger->info("Watermarked file: $watermarked_file");

# Step 4: Verify watermarked file
if ($frobnitz->verify_file($watermarked_file)) {
    pass("✅ Watermarked file verification passed");
    $logger->info("Verified watermarked file: $watermarked_file");
} else {
    fail("❌ Watermarked file verification failed");
    $logger->fatal("Verification failed for: $watermarked_file");
    BAIL_OUT("Aborting test after failed watermark verification.");
}

done_testing();
